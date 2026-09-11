"""Tests for HTTP API authentication and standardized error handling."""

import json
from pathlib import Path
import time
import urllib.error
import urllib.request
import pytest

from terminal_session_manager.api.server import APIServer
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
def auth_api_server(tmp_path: Path) -> APIServer:
    db_file = tmp_path / "api_auth_test.db"
    storage = SqliteStorage(db_file)
    session_repo = SqliteSessionRepository(storage)
    event_repo = SqliteEventRepository(storage)
    job_repo = SqliteJobRepository(storage)
    dev_repo = SqliteDeviceRepository(storage)
    cred_store = ProtectedLocalCredentialStore(storage, master_key="TEST_API_KEY_AUTH")

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
        api_token="LOCAL_SECRET_KEY_987654",
    )
    server.start_in_thread()
    time.sleep(0.1)

    yield server

    server.stop()
    session_service.close_all()
    storage.close()


def test_api_authentication_enforcement(auth_api_server: APIServer) -> None:
    base = auth_api_server.base_url

    # 1. No auth headers -> 401 Unauthorized
    status, err = http_request(f"{base}/sessions", method="GET")
    assert status == 401
    assert err["error"] == "Unauthorized"

    # 2. Invalid Bearer token -> 401 Unauthorized
    status, err = http_request(
        f"{base}/sessions",
        method="GET",
        headers={"Authorization": "Bearer WRONG_TOKEN"},
    )
    assert status == 401
    assert err["error"] == "Unauthorized"

    # 3. Valid Bearer token -> 200 OK
    status, data = http_request(
        f"{base}/sessions",
        method="GET",
        headers={"Authorization": "Bearer LOCAL_SECRET_KEY_987654"},
    )
    assert status == 200
    assert "items" in data

    # 4. Valid X-API-Key header -> 200 OK
    status, data = http_request(
        f"{base}/sessions",
        method="GET",
        headers={"X-API-Key": "LOCAL_SECRET_KEY_987654"},
    )
    assert status == 200
    assert "items" in data


def test_api_standardized_error_handling(auth_api_server: APIServer) -> None:
    base = auth_api_server.base_url
    auth_headers = {"Authorization": "Bearer LOCAL_SECRET_KEY_987654"}

    # 1. Route not found -> 404 RouteNotFound
    status, err = http_request(f"{base}/non-existent-route", method="GET", headers=auth_headers)
    assert status == 404
    assert err["error"] == "RouteNotFound"

    # 2. Session not found -> 404 SessionNotFoundError
    status, err = http_request(f"{base}/sessions/invalid-session-id", method="GET", headers=auth_headers)
    assert status == 404
    assert err["error"] == "SessionNotFoundError"

    # 3. Device not found -> 404 DeviceNotFoundError
    status, err = http_request(f"{base}/devices/invalid-device-name", method="GET", headers=auth_headers)
    assert status == 404
    assert err["error"] == "DeviceNotFoundError"

    # 4. Validation error (missing required fields) -> 400 ValidationError
    status, err = http_request(f"{base}/devices", method="POST", body={}, headers=auth_headers)
    assert status == 400
    assert err["error"] == "ValidationError"
