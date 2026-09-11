"""Tests for Sessions and Events HTTP API endpoints."""

import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import pytest

from terminal_session_manager.api.server import APIServer
from terminal_session_manager.models.session import SessionStatus
from terminal_session_manager.persistence.sqlite import (
    SqliteDeviceRepository,
    SqliteEventRepository,
    SqliteJobRepository,
    SqliteSessionRepository,
    SqliteStorage,
)
from terminal_session_manager.services.credential_store import ProtectedLocalCredentialStore
from terminal_session_manager.services.device_service import DeviceService
from terminal_session_manager.services.job_service import JobService
from terminal_session_manager.services.session_service import SessionService


def http_request(
    url: str,
    method: str = "GET",
    body: dict | None = None,
    headers: dict | None = None,
) -> tuple[int, dict]:
    """Helper to perform HTTP JSON requests using standard library urllib."""
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    data_bytes = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            data = json.loads(content) if content else {}
            return status, data
    except urllib.error.HTTPError as err:
        status = err.code
        content = err.read().decode("utf-8")
        data = json.loads(content) if content else {}
        return status, data


@pytest.fixture
def api_server(tmp_path: Path) -> APIServer:
    db_file = tmp_path / "api_session_test.db"
    storage = SqliteStorage(db_file)
    session_repo = SqliteSessionRepository(storage)
    event_repo = SqliteEventRepository(storage)
    job_repo = SqliteJobRepository(storage)
    dev_repo = SqliteDeviceRepository(storage)
    cred_store = ProtectedLocalCredentialStore(storage, master_key="TEST_API_KEY_123")

    dev_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)
    job_service = JobService(job_repo=job_repo, event_repo=event_repo, session_repo=session_repo)
    session_service = SessionService(session_repo=session_repo, event_repo=event_repo, device_service=dev_service)

    server = APIServer(
        session_service=session_service,
        job_service=job_service,
        device_service=dev_service,
        event_repo=event_repo,
        host="127.0.0.1",
        port=0,
        api_token=None,
    )
    server.start_in_thread()
    time.sleep(0.1)

    yield server

    server.stop()
    session_service.close_all()
    storage.close()


def test_session_lifecycle_and_io_api(api_server: APIServer) -> None:
    base = api_server.base_url

    # 1. Create session via POST /sessions
    status, data = http_request(f"{base}/sessions", method="POST", body={"name": "interactive-term-1"})
    assert status == 201
    assert "id" in data
    assert data["name"] == "interactive-term-1"
    assert data["status"] == SessionStatus.RUNNING.value
    session_id = data["id"]

    # 2. Get session via GET /sessions/{id}
    status, data = http_request(f"{base}/sessions/{session_id}", method="GET")
    assert status == 200
    assert data["id"] == session_id
    assert data["status"] == SessionStatus.RUNNING.value

    # 3. List sessions via GET /sessions
    status, data = http_request(f"{base}/sessions", method="GET")
    assert status == 200
    assert data["total"] >= 1
    session_ids = [s["id"] for s in data["items"]]
    assert session_id in session_ids

    # 4. Write to session via POST /sessions/{id}/write
    status, data = http_request(
        f"{base}/sessions/{session_id}/write",
        method="POST",
        body={"data": "echo 'hello from http api'\n"},
    )
    assert status == 200
    assert data["bytes_written"] > 0

    # 5. Read from session via POST /sessions/{id}/read
    time.sleep(0.2)
    status, data = http_request(
        f"{base}/sessions/{session_id}/read",
        method="POST",
        body={"max_bytes": 4096, "timeout": 0.5},
    )
    assert status == 200
    assert data["session_id"] == session_id

    # 6. Close session via POST /sessions/{id}/close
    status, data = http_request(f"{base}/sessions/{session_id}/close", method="POST")
    assert status == 200
    assert data["status"] == SessionStatus.CLOSED.value

    # 7. Write to closed session returns 409 Conflict
    status, data = http_request(
        f"{base}/sessions/{session_id}/write",
        method="POST",
        body={"data": "ls\n"},
    )
    assert status == 409
    assert data["error"] == "TransportClosedError"


def test_events_cursor_pagination_api(api_server: APIServer) -> None:
    base = api_server.base_url

    # Create session and write multiple commands
    status, data = http_request(f"{base}/sessions", method="POST", body={"name": "events-test"})
    session_id = data["id"]

    for i in range(5):
        http_request(
            f"{base}/sessions/{session_id}/write",
            method="POST",
            body={"data": f"echo line {i}\n"},
        )
        time.sleep(0.05)

    # Read events with cursor: since_sequence=0, limit=2
    status, data = http_request(f"{base}/sessions/{session_id}/events?since_sequence=0&limit=2")
    assert status == 200
    assert len(data["items"]) == 2
    assert data["since_sequence"] == 0
    seq0 = data["items"][0]["sequence"]
    seq1 = data["items"][1]["sequence"]
    assert seq1 > seq0

    # Read next batch using cursor: since_sequence=seq1 + 1
    next_cursor = seq1 + 1
    status, data = http_request(f"{base}/sessions/{session_id}/events?since_sequence={next_cursor}&limit=10")
    assert status == 200
    assert all(e["sequence"] >= next_cursor for e in data["items"])

    # Clean up
    http_request(f"{base}/sessions/{session_id}/close", method="POST")
