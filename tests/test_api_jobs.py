"""Tests for Jobs HTTP API endpoints."""

import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import pytest

from terminal_session_manager.api.server import APIServer
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
def api_server(tmp_path: Path) -> APIServer:
    db_file = tmp_path / "api_jobs_test.db"
    storage = SqliteStorage(db_file)
    session_repo = SqliteSessionRepository(storage)
    event_repo = SqliteEventRepository(storage)
    job_repo = SqliteJobRepository(storage)
    dev_repo = SqliteDeviceRepository(storage)
    cred_store = ProtectedLocalCredentialStore(storage, master_key="TEST_API_KEY_JOBS")

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


def test_job_submit_wait_and_query_api(api_server: APIServer) -> None:
    base = api_server.base_url

    # Create session
    status, sess = http_request(f"{base}/sessions", method="POST", body={"name": "job-runner-session"})
    session_id = sess["id"]

    # 1. Submit job via POST /sessions/{id}/jobs
    cmd = f"{sys.executable} -c \"print('job output test')\""
    status, job_data = http_request(
        f"{base}/sessions/{session_id}/jobs",
        method="POST",
        body={"command": cmd},
    )
    assert status == 202
    assert "id" in job_data
    job_id = job_data["id"]
    assert job_data["session_id"] == session_id

    # 2. Wait for job via POST /jobs/{id}/wait
    status, completed_job = http_request(
        f"{base}/jobs/{job_id}/wait",
        method="POST",
        body={"timeout": 5.0},
    )
    assert status == 200
    assert completed_job["status"] == JobStatus.COMPLETED.value
    assert completed_job["exit_code"] == 0
    assert "job output test" in completed_job["stdout"]

    # 3. Query job via GET /jobs/{id}
    status, fetched_job = http_request(f"{base}/jobs/{job_id}", method="GET")
    assert status == 200
    assert fetched_job["id"] == job_id
    assert fetched_job["status"] == JobStatus.COMPLETED.value

    # 4. List jobs via GET /sessions/{id}/jobs
    status, job_list = http_request(f"{base}/sessions/{session_id}/jobs", method="GET")
    assert status == 200
    assert job_list["total"] >= 1
    assert any(j["id"] == job_id for j in job_list["items"])


def test_job_cancellation_api(api_server: APIServer) -> None:
    base = api_server.base_url

    status, sess = http_request(f"{base}/sessions", method="POST", body={"name": "job-cancel-session"})
    session_id = sess["id"]

    # Submit a long-running job (sleep 10 seconds)
    cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
    status, job_data = http_request(
        f"{base}/jobs",
        method="POST",
        body={"session_id": session_id, "command": cmd},
    )
    assert status == 202
    job_id = job_data["id"]


    time.sleep(0.3)

    # Cancel via POST /jobs/{id}/cancel
    status, cancelled_job = http_request(f"{base}/jobs/{job_id}/cancel", method="POST")
    assert status == 200
    assert cancelled_job["status"] == JobStatus.CANCELLED.value
