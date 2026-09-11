"""Tests for FastMCP server implementation in Terminal Session Manager."""

from __future__ import annotations

import asyncio
import sys

from fastmcp.client import Client
from fastmcp.exceptions import ToolError
import pytest

from terminal_session_manager.mcp import create_mcp_server
from terminal_session_manager.models import ConnectionMethod, CredentialRef, CredentialType, DeviceType
from terminal_session_manager.persistence.sqlite import SqliteDeviceRepository, SqliteStorage
from terminal_session_manager.services.credential_store import ProtectedLocalCredentialStore
from terminal_session_manager.services.device_service import DeviceService


def _run(coro):
    """Helper to run async coroutines in synchronous pytest tests."""
    return asyncio.run(coro)


def test_mcp_server_lists_all_expected_tools():
    async def _test():
        mcp = create_mcp_server(db_path=":memory:")
        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}

            expected_tools = {
                # Sessions
                "create_session",
                "get_session",
                "list_sessions",
                "write_session",
                "read_session",
                "close_session",
                # Events
                "get_events",
                # Jobs
                "submit_job",
                "get_job",
                "list_jobs",
                "wait_job",
                "cancel_job",
                # Devices
                "list_devices",
                "get_device",
                "resolve_device",
            }
            assert expected_tools.issubset(tool_names)

    _run(_test())


def test_mcp_session_lifecycle():
    async def _test():
        mcp = create_mcp_server(db_path=":memory:")
        async with Client(mcp) as client:
            # 1. Create session
            res = await client.call_tool("create_session", {"name": "mcp-test-session"})
            session_data = res.data
            assert session_data["name"] == "mcp-test-session"
            assert session_data["status"] == "running"
            session_id = session_data["id"]

            # 2. Get session
            res_get = await client.call_tool("get_session", {"session_id": session_id})
            assert res_get.data["id"] == session_id
            assert res_get.data["status"] == "running"

            # 3. List sessions
            res_list = await client.call_tool("list_sessions", {})
            assert any(s["id"] == session_id for s in res_list.data)

            # 4. Write to session
            res_write = await client.call_tool("write_session", {
                "session_id": session_id,
                "data": "echo hello_mcp\n",
            })
            assert res_write.data["bytes_written"] > 0

            # Allow shell to process
            await asyncio.sleep(0.3)

            # 5. Read from session
            res_read = await client.call_tool("read_session", {
                "session_id": session_id,
                "timeout": 1.0,
            })
            assert "data" in res_read.data
            assert isinstance(res_read.data["data"], str)

            # 6. Close session
            res_close = await client.call_tool("close_session", {"session_id": session_id})
            assert res_close.data["status"] == "closed"

            # Verify closed state via get_session
            res_get_closed = await client.call_tool("get_session", {"session_id": session_id})
            assert res_get_closed.data["status"] == "closed"

    _run(_test())


def test_mcp_events_cursor_pagination():
    async def _test():
        mcp = create_mcp_server(db_path=":memory:")
        async with Client(mcp) as client:
            sess = await client.call_tool("create_session", {"name": "events-test"})
            session_id = sess.data["id"]

            await client.call_tool("write_session", {"session_id": session_id, "data": "echo 1\n"})
            await asyncio.sleep(0.2)
            await client.call_tool("write_session", {"session_id": session_id, "data": "echo 2\n"})
            await asyncio.sleep(0.2)

            # Get all events
            events_all = await client.call_tool("get_events", {"session_id": session_id})
            items = events_all.data["items"]
            assert len(items) >= 2

            # Paginate with limit
            events_page1 = await client.call_tool("get_events", {
                "session_id": session_id,
                "limit": 2,
            })
            items_page1 = events_page1.data["items"]
            assert len(items_page1) == 2

            # Paginate with since_sequence
            seq2 = items_page1[1]["sequence"]
            events_page2 = await client.call_tool("get_events", {
                "session_id": session_id,
                "since_sequence": seq2,
            })
            for ev in events_page2.data["items"]:
                assert ev["sequence"] >= seq2

    _run(_test())


def test_mcp_job_lifecycle_and_wait():
    async def _test():
        mcp = create_mcp_server(db_path=":memory:")
        async with Client(mcp) as client:
            # Create session for job
            sess = await client.call_tool("create_session", {"name": "job-session"})
            session_id = sess.data["id"]

            # Submit python one-liner job as string command
            cmd = f'"{sys.executable}" -c "import sys; print(\'job_mcp_output\'); sys.exit(0)"'
            res = await client.call_tool("submit_job", {
                "session_id": session_id,
                "command": cmd,
                "timeout": 10.0,
            })
            job_data = res.data
            job_id = job_data["id"]
            assert job_data["status"] in ("pending", "running")

            # Get job
            res_get = await client.call_tool("get_job", {"job_id": job_id})
            assert res_get.data["id"] == job_id

            # List jobs
            res_list = await client.call_tool("list_jobs", {"session_id": session_id})
            assert any(j["id"] == job_id for j in res_list.data)

            # Wait job completion
            res_wait = await client.call_tool("wait_job", {
                "job_id": job_id,
                "timeout": 10.0,
            })
            assert res_wait.data["status"] == "completed"
            assert res_wait.data["exit_code"] == 0

    _run(_test())


def test_mcp_job_cancel():
    async def _test():
        mcp = create_mcp_server(db_path=":memory:")
        async with Client(mcp) as client:
            sess = await client.call_tool("create_session", {"name": "job-cancel-session"})
            session_id = sess.data["id"]

            # Start a long-running job
            cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
            res = await client.call_tool("submit_job", {
                "session_id": session_id,
                "command": cmd,
                "timeout": 30.0,
            })
            job_id = res.data["id"]

            # Small pause to let process start
            await asyncio.sleep(0.3)

            # Cancel job
            res_cancel = await client.call_tool("cancel_job", {"job_id": job_id})
            assert res_cancel.data["status"] == "cancelled"

            # Wait job should return immediately with cancelled status
            res_wait = await client.call_tool("wait_job", {"job_id": job_id, "timeout": 2.0})
            assert res_wait.data["status"] == "cancelled"

    _run(_test())


def test_mcp_devices_and_secret_protection():
    async def _test():
        storage = SqliteStorage(":memory:")
        dev_repo = SqliteDeviceRepository(storage)
        cred_store = ProtectedLocalCredentialStore(storage)
        dev_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)

        # Store secret credential
        cred_ref = CredentialRef(name="sw-cred", credential_type=CredentialType.PASSWORD)
        cred_store.save_credential(cred_ref, "super-secret-mcp-password")

        # Register device with credential reference
        dev_service.create_device(
            name="sw-core",
            host="192.168.10.1",
            port=22,
            device_type=DeviceType.SWITCH,
            connection_method=ConnectionMethod.SSH,
            credential_ref_id=cred_ref.id,
            default_user="admin",
        )

        mcp = create_mcp_server(storage=storage, device_service=dev_service)
        async with Client(mcp) as client:
            # 1. List devices
            res_list = await client.call_tool("list_devices", {})
            assert len(res_list.data) == 1
            dev_info = res_list.data[0]
            assert dev_info["name"] == "sw-core"
            assert "password" not in str(dev_info)

            # 2. Get device by nickname/name
            res_get = await client.call_tool("get_device", {"name_or_id": "sw-core"})
            assert res_get.data["host"] == "192.168.10.1"
            assert "password" not in str(res_get.data)

            # 3. Resolve device
            res_resolve = await client.call_tool("resolve_device", {"name_or_id": "sw-core"})
            resolve_data = res_resolve.data
            assert resolve_data["device_name"] == "sw-core"
            assert resolve_data["host"] == "192.168.10.1"
            assert resolve_data["port"] == 22
            assert resolve_data["connection_method"] == "ssh"
            assert resolve_data["default_user"] == "admin"
            assert resolve_data["has_credential"] is True

            # CRITICAL SECURITY CHECK: Raw password must NEVER appear in tool result
            raw_result_str = str(resolve_data)
            assert "super-secret-mcp-password" not in raw_result_str
            assert "password" not in resolve_data

    _run(_test())


def test_mcp_error_handling_unknown_entities():
    async def _test():
        mcp = create_mcp_server(db_path=":memory:")
        async with Client(mcp) as client:
            # Non-existent session
            with pytest.raises(ToolError) as exc_sess:
                await client.call_tool("get_session", {"session_id": "nonexistent-id"})
            assert "Session with ID 'nonexistent-id' was not found" in str(exc_sess.value)

            # Non-existent job
            with pytest.raises(ToolError) as exc_job:
                await client.call_tool("get_job", {"job_id": "nonexistent-job"})
            assert "Job with ID 'nonexistent-job' was not found" in str(exc_job.value)

            # Non-existent device
            with pytest.raises(ToolError) as exc_dev:
                await client.call_tool("get_device", {"name_or_id": "unknown-dev"})
            assert "unknown-dev" in str(exc_dev.value)

    _run(_test())


def test_mcp_device_inactive_rejection():
    async def _test():
        storage = SqliteStorage(":memory:")
        dev_repo = SqliteDeviceRepository(storage)
        dev_service = DeviceService(repository=dev_repo)
        device = dev_service.create_device(
            name="r-old",
            host="10.0.0.1",
            port=22,
            device_type=DeviceType.ROUTER,
            connection_method=ConnectionMethod.SSH,
        )
        dev_service.deactivate_device(device.id)

        mcp = create_mcp_server(storage=storage, device_service=dev_service)
        async with Client(mcp) as client:
            with pytest.raises(ToolError) as exc:
                await client.call_tool("resolve_device", {"name_or_id": "r-old"})
            assert "inactive" in str(exc.value).lower()

    _run(_test())
