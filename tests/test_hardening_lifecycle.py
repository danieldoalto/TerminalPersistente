"""Tests for lifecycle hardening, graceful shutdown, credential rotation, and orphan recovery."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import time

from fastmcp.client import Client
import pytest

from terminal_session_manager.app import TSMApplication
from terminal_session_manager.config import TSMConfig
from terminal_session_manager.errors import CredentialResolutionError
from terminal_session_manager.models import (
    CredentialRef,
    CredentialType,
    Job,
    JobStatus,
    Session,
    SessionStatus,
)
from terminal_session_manager.persistence.sqlite import SqliteStorage
from terminal_session_manager.services.credential_store import ProtectedLocalCredentialStore


def _run(coro):
    return asyncio.run(coro)


def test_recover_orphaned_sessions_and_jobs_on_startup(tmp_path: Path):
    db_file = str(tmp_path / "orphan_recovery.db")

    # 1. Seed database with orphaned session and job as if server crashed while running
    storage = SqliteStorage(db_file)
    from terminal_session_manager.persistence.sqlite import (
        SqliteEventRepository,
        SqliteJobRepository,
        SqliteSessionRepository,
    )

    session_repo = SqliteSessionRepository(storage)
    job_repo = SqliteJobRepository(storage)

    orphaned_session = Session(id="orphaned-sess-1", name="orphaned-session")
    orphaned_session.transition_to(SessionStatus.RUNNING)
    session_repo.save(orphaned_session)

    orphaned_job = Job(id="orphaned-job-1", session_id="orphaned-sess-1", command="sleep 100")
    orphaned_job.transition_to(JobStatus.RUNNING)
    job_repo.save(orphaned_job)

    storage.close()

    # 2. Start a new application instance on the same database
    config = TSMConfig()
    config.storage.db_path = db_file
    config.jobs.recover_orphaned_on_start = True

    app = TSMApplication(config)
    report = app.startup()

    assert report["recovered_jobs"] >= 1
    assert report["recovered_sessions"] >= 1

    # 3. Verify states transitioned safely
    recovered_sess = app.session_repo.get_by_id("orphaned-sess-1")
    assert recovered_sess is not None
    assert recovered_sess.status == SessionStatus.LOST

    recovered_job = app.job_repo.get_by_id("orphaned-job-1")
    assert recovered_job is not None
    assert recovered_job.status == JobStatus.FAILED
    assert "interrupted" in (recovered_job.failure_reason or "").lower()

    app.shutdown()


def test_graceful_shutdown_closes_active_sessions(tmp_path: Path):
    db_file = str(tmp_path / "shutdown_test.db")
    config = TSMConfig()
    config.storage.db_path = db_file
    config.sessions.cleanup_on_shutdown = True

    app = TSMApplication(config)
    app.startup()

    local_sess = app.session_service.create_session(name="live-session")
    sess_id = local_sess.session.id
    assert local_sess.session.status == SessionStatus.RUNNING

    # Shutdown should terminate session process and close SQLite
    app.shutdown()

    # Verify session is marked CLOSED in database
    storage_recheck = SqliteStorage(db_file)
    from terminal_session_manager.persistence.sqlite import SqliteSessionRepository
    repo = SqliteSessionRepository(storage_recheck)
    persisted = repo.get_by_id(sess_id)
    assert persisted is not None
    assert persisted.status == SessionStatus.CLOSED
    storage_recheck.close()


def test_credential_store_rotate_master_key(tmp_path: Path):
    db_file = str(tmp_path / "key_rotation.db")
    storage = SqliteStorage(db_file)

    initial_master_key = "initial-secret-key-12345678"
    new_master_key = "new-rotated-secret-key-87654321"

    store = ProtectedLocalCredentialStore(storage, master_key=initial_master_key)

    # Store credentials
    ref1 = CredentialRef(name="c1", credential_type=CredentialType.PASSWORD)
    store.save_credential(ref1, "my-super-secret-password-1")

    ref2 = CredentialRef(name="c2", credential_type=CredentialType.TOKEN)
    store.save_credential(ref2, "api-token-value-2")

    # Verify initial resolution
    assert store.resolve(ref1.id) == "my-super-secret-password-1"
    assert store.resolve(ref2.id) == "api-token-value-2"

    # Rotate master key
    rotated_count = store.rotate_master_key(new_master_key)
    assert rotated_count == 2

    # Verify resolution with new key on current store
    assert store.resolve(ref1.id) == "my-super-secret-password-1"
    assert store.resolve(ref2.id) == "api-token-value-2"

    # Instantiate new store with new master key directly from database
    store_new = ProtectedLocalCredentialStore(storage, master_key=new_master_key)
    assert store_new.resolve(ref1.id) == "my-super-secret-password-1"
    assert store_new.resolve(ref2.id) == "api-token-value-2"

    # Instantiate store with old master key -> must fail integrity check
    store_old = ProtectedLocalCredentialStore(storage, master_key=initial_master_key)
    with pytest.raises(CredentialResolutionError, match="Integrity check failed"):
        store_old.resolve(ref1.id)

    storage.close()


def test_credential_store_rotate_credential(tmp_path: Path):
    db_file = str(tmp_path / "cred_rotation.db")
    storage = SqliteStorage(db_file)
    store = ProtectedLocalCredentialStore(storage)

    ref = CredentialRef(name="db-pwd", credential_type=CredentialType.PASSWORD)
    store.save_credential(ref, "initial-password")
    assert store.resolve(ref.id) == "initial-password"

    # Rotate password
    store.rotate_credential(ref.id, "rotated-password-updated")
    assert store.resolve(ref.id) == "rotated-password-updated"

    storage.close()


def test_clean_installation_creates_db_directory(tmp_path: Path):
    # Deep nested path that does not yet exist
    nested_db = tmp_path / "deep" / "nested" / "dir" / "clean_install.db"
    assert not nested_db.parent.exists()

    config = TSMConfig()
    config.storage.db_path = str(nested_db)

    app = TSMApplication(config)
    app.startup()

    assert nested_db.parent.exists()
    assert nested_db.is_file()

    # Can register session and query
    s = app.session_service.create_session(name="install-test")
    assert s.session.id is not None
    assert app.session_service.get_session(s.session.id) is not None

    app.shutdown()


def test_api_and_mcp_share_same_database_and_configuration(tmp_path: Path):
    db_file = str(tmp_path / "shared_app.db")
    config = TSMConfig()
    config.storage.db_path = db_file

    app = TSMApplication(config)
    app.startup()

    # 1. Create a session via domain service in app
    session = app.session_service.create_session(name="shared-session")
    session_id = session.session.id

    # 2. Query via MCP server created from same app
    mcp = app.create_mcp_server()

    async def _mcp_test():
        async with Client(mcp) as client:
            res = await client.call_tool("get_session", {"session_id": session_id})
            assert res.data["id"] == session_id
            assert res.data["name"] == "shared-session"

    _run(_mcp_test())

    # 3. Query via APIServer created from same app
    api_server = app.create_api_server()
    thread = api_server.start_in_thread()
    time.sleep(0.1)

    import urllib.request
    import json

    url = f"{api_server.base_url}/sessions/{session_id}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data["id"] == session_id
        assert data["name"] == "shared-session"

    api_server.stop()
    app.shutdown()
