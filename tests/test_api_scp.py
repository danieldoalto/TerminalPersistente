"""Tests for SCP HTTP API and FastMCP tools."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

from fastmcp.client import Client
import pytest

from terminal_session_manager.api.server import APIServer
from terminal_session_manager.config import SSHConfig
from terminal_session_manager.mcp import create_mcp_server
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.models.job import JobStatus
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
from terminal_session_manager.services.scp_service import SCPService
from terminal_session_manager.services.session_service import SessionService
from tests.test_scp_service import MockSCPClient
from tests.test_ssh_transport import MockSSHClient


def http_request(
    url: str,
    method: str = "GET",
    body: dict | None = None,
    headers: dict | None = None,
) -> tuple[int, dict]:
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
def scp_api_server(tmp_path: Path):
    db_file = tmp_path / "api_scp_test.db"
    storage = SqliteStorage(db_file)
    session_repo = SqliteSessionRepository(storage)
    event_repo = SqliteEventRepository(storage)
    job_repo = SqliteJobRepository(storage)
    dev_repo = SqliteDeviceRepository(storage)
    cred_store = ProtectedLocalCredentialStore(storage, master_key="TEST_API_KEY_SCP_32_CHARS_LONG")

    dev_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)
    ssh_cfg = SSHConfig(strict_host_key_checking=False, connect_timeout=5.0)

    # Register an SSH device
    cred = CredentialRef(name="api-ssh-pass", credential_type=CredentialType.PASSWORD)
    cred_store.save_credential(cred, "secret_password_for_api_123")

    device = Device(
        name="api-remote",
        host="10.0.0.50",
        port=22,
        device_type=DeviceType.SERVER,
        connection_method=ConnectionMethod.SSH,
        default_user="ubuntu",
        credential_ref_id=cred.id,
    )
    dev_service.register_device(device)

    def mock_cli_factory():
        return MockSSHClient()

    def mock_scp_factory(transport, **kwargs):
        return MockSCPClient(transport, **kwargs)

    scp_service = SCPService(
        device_service=dev_service,
        job_repo=job_repo,
        event_repo=event_repo,
        session_repo=session_repo,
        ssh_config=ssh_cfg,
        client_factory=mock_cli_factory,
        scp_factory=mock_scp_factory,
    )

    job_service = JobService(
        job_repo=job_repo,
        event_repo=event_repo,
        session_repo=session_repo,
        device_service=dev_service,
        ssh_config=ssh_cfg,
        scp_service=scp_service,
    )

    session_service = SessionService(
        session_repo=session_repo,
        event_repo=event_repo,
        device_service=dev_service,
        ssh_config=ssh_cfg,
    )

    server = APIServer(
        session_service=session_service,
        job_service=job_service,
        device_service=dev_service,
        event_repo=event_repo,
        scp_service=scp_service,
        host="127.0.0.1",
        port=0,
    )
    server.start_in_thread()

    yield {
        "server": server,
        "base_url": server.base_url,
        "tmp_path": tmp_path,
        "scp_service": scp_service,
        "job_service": job_service,
    }

    server.stop()


def test_api_scp_upload(scp_api_server):
    base_url = scp_api_server["base_url"]
    tmp_path = scp_api_server["tmp_path"]

    local_file = tmp_path / "hello.txt"
    local_file.write_text("hello world from api", encoding="utf-8")

    payload = {
        "device": "api-remote",
        "local_path": str(local_file),
        "remote_path": "/var/tmp/hello.txt",
    }

    status, data = http_request(f"{base_url}/scp/upload", method="POST", body=payload)
    assert status == 202
    assert "id" in data
    assert data["metadata"]["direction"] == "upload"
    assert "secret_password_for_api_123" not in json.dumps(data)

    # Wait for completion via job service
    finished = scp_api_server["scp_service"].wait_transfer(data["id"], timeout=3.0)
    assert finished.status == JobStatus.COMPLETED
    assert finished.exit_code == 0


def test_api_scp_download(scp_api_server):
    base_url = scp_api_server["base_url"]
    tmp_path = scp_api_server["tmp_path"]

    dest_file = tmp_path / "downloaded_hello.txt"

    payload = {
        "device": "api-remote",
        "remote_path": "/var/tmp/hello.txt",
        "local_path": str(dest_file),
    }

    status, data = http_request(f"{base_url}/scp/download", method="POST", body=payload)
    assert status == 202
    assert data["metadata"]["direction"] == "download"

    finished = scp_api_server["scp_service"].wait_transfer(data["id"], timeout=3.0)
    assert finished.status == JobStatus.COMPLETED
    assert dest_file.is_file()


def test_api_scp_validations(scp_api_server):
    base_url = scp_api_server["base_url"]

    # Missing device
    status, data = http_request(
        f"{base_url}/scp/upload",
        method="POST",
        body={"local_path": "a", "remote_path": "b"},
    )
    assert status == 400
    assert "ValidationError" in data.get("error", "")

    # Missing local_path
    status, data = http_request(
        f"{base_url}/scp/upload",
        method="POST",
        body={"device": "api-remote", "remote_path": "b"},
    )
    assert status == 400

    # Non-existent local file
    status, data = http_request(
        f"{base_url}/scp/upload",
        method="POST",
        body={"device": "api-remote", "local_path": "/path/does/not/exist/999.txt", "remote_path": "/tmp/b"},
    )
    assert status == 400


def test_mcp_scp_tools_registered_and_callable(tmp_path: Path):
    async def _test():
        storage = SqliteStorage(":memory:")
        dev_repo = SqliteDeviceRepository(storage)
        event_repo = SqliteEventRepository(storage)
        job_repo = SqliteJobRepository(storage)
        session_repo = SqliteSessionRepository(storage)
        cred_store = ProtectedLocalCredentialStore(storage, master_key="test-master-key-32-chars-long!!")
        dev_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)

        device = Device(
            name="mcp-srv",
            host="192.168.1.200",
            port=22,
            connection_method=ConnectionMethod.SSH,
        )
        dev_service.register_device(device)

        def mock_cli_factory():
            return MockSSHClient()

        def mock_scp_factory(transport, **kwargs):
            return MockSCPClient(transport, **kwargs)

        scp_service = SCPService(
            device_service=dev_service,
            job_repo=job_repo,
            event_repo=event_repo,
            session_repo=session_repo,
            client_factory=mock_cli_factory,
            scp_factory=mock_scp_factory,
        )

        job_service = JobService(
            job_repo=job_repo,
            event_repo=event_repo,
            session_repo=session_repo,
            device_service=dev_service,
            scp_service=scp_service,
        )

        session_service = SessionService(
            session_repo=session_repo,
            event_repo=event_repo,
            device_service=dev_service,
        )

        mcp = create_mcp_server(
            session_service=session_service,
            job_service=job_service,
            device_service=dev_service,
            event_repo=event_repo,
            scp_service=scp_service,
            storage=storage,
        )

        local_file = tmp_path / "mcp_upload.txt"
        local_file.write_text("content for mcp", encoding="utf-8")

        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert "scp_upload" in tool_names
            assert "scp_download" in tool_names

            # Call scp_upload tool
            res = await client.call_tool(
                "scp_upload",
                {
                    "device": "mcp-srv",
                    "local_path": str(local_file),
                    "remote_path": "/remote/mcp_upload.txt",
                },
            )
            data = res.data
            assert "id" in data
            assert data["metadata"]["direction"] == "upload"

    asyncio.run(_test())
