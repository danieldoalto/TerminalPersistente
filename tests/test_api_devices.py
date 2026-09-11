"""Tests for Devices HTTP API endpoints and safe nickname resolution."""

import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import pytest

from terminal_session_manager.api.server import APIServer
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, DeviceType
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
def api_server_with_creds(tmp_path: Path) -> tuple[APIServer, ProtectedLocalCredentialStore]:
    db_file = tmp_path / "api_devices_test.db"
    storage = SqliteStorage(db_file)
    session_repo = SqliteSessionRepository(storage)
    event_repo = SqliteEventRepository(storage)
    job_repo = SqliteJobRepository(storage)
    dev_repo = SqliteDeviceRepository(storage)
    cred_store = ProtectedLocalCredentialStore(storage, master_key="TEST_API_KEY_DEVICES")

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

    yield server, cred_store

    server.stop()
    session_service.close_all()
    storage.close()


def test_device_crud_and_safe_resolution_api(
    api_server_with_creds: tuple[APIServer, ProtectedLocalCredentialStore],
) -> None:
    server, cred_store = api_server_with_creds
    base = server.base_url

    # Save a secret into the protected store
    secret_value = "CONFIDENTIAL_PASSWORD_998811"
    cred = CredentialRef(name="bastion-admin-key", credential_type=CredentialType.SSH_KEY)
    cred_store.save_credential(cred, secret_value)

    # 1. Create device via POST /devices
    status, dev_data = http_request(
        f"{base}/devices",
        method="POST",
        body={
            "name": "core-firewall",
            "host": "192.168.1.1",
            "port": 2222,
            "device_type": DeviceType.ROUTER.value,
            "connection_method": ConnectionMethod.SSH.value,
            "default_user": "secops",
            "options": {"strict_host_key_checking": False},
            "credential_ref_id": cred.id,
        },
    )
    assert status == 201
    assert dev_data["name"] == "core-firewall"
    device_id = dev_data["id"]

    # 2. Get device by nickname via GET /devices/{name}
    status, fetched = http_request(f"{base}/devices/core-firewall", method="GET")
    assert status == 200
    assert fetched["id"] == device_id
    assert fetched["host"] == "192.168.1.1"

    # 3. List devices via GET /devices
    status, dev_list = http_request(f"{base}/devices", method="GET")
    assert status == 200
    assert dev_list["total"] >= 1
    assert any(d["name"] == "core-firewall" for d in dev_list["items"])

    # 4. Resolve connection by nickname via GET /devices/{name}/resolve
    status, resolved = http_request(f"{base}/devices/core-firewall/resolve", method="GET")
    assert status == 200
    assert resolved["device_name"] == "core-firewall"
    assert resolved["host"] == "192.168.1.1"
    assert resolved["port"] == 2222
    assert resolved["default_user"] == "secops"
    assert resolved["has_credential"] is True
    assert resolved["credential_ref_id"] == cred.id

    # CRITICAL SECURITY CHECK: Ensure secret NEVER appears in API response
    raw_response_text = json.dumps(resolved)
    assert secret_value not in raw_response_text
    assert "password" not in resolved
    assert "secret" not in resolved

    # 5. Update device via PATCH /devices/{id}
    status, updated = http_request(
        f"{base}/devices/{device_id}",
        method="PATCH",
        body={"port": 22222, "default_user": "root"},
    )
    assert status == 200
    assert updated["port"] == 22222
    assert updated["default_user"] == "root"

    # 6. Deactivate device via POST /devices/{id}/deactivate
    status, deact = http_request(f"{base}/devices/{device_id}/deactivate", method="POST")
    assert status == 200
    assert deact["is_active"] is False

    # 7. Resolving deactivated device must fail with 400 Bad Request
    status, err_data = http_request(f"{base}/devices/core-firewall/resolve", method="GET")
    assert status == 400
    assert "DeviceInactiveError" in err_data["error"] or "inactive" in err_data["message"]
