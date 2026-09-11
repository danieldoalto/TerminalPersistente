"""Tests for OpenAPI specification and Swagger UI documentation endpoints."""

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


def raw_http_get(url: str, headers: dict | None = None) -> tuple[int, str, str]:
    """Helper returning (status_code, content_type, body_text)."""
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read().decode("utf-8")
            return resp.status, content_type, body
    except urllib.error.HTTPError as err:
        content_type = err.headers.get("Content-Type", "")
        body = err.read().decode("utf-8")
        return err.code, content_type, body


@pytest.fixture
def doc_api_server(tmp_path: Path) -> APIServer:
    db_file = tmp_path / "api_doc_test.db"
    storage = SqliteStorage(db_file)
    session_repo = SqliteSessionRepository(storage)
    event_repo = SqliteEventRepository(storage)
    job_repo = SqliteJobRepository(storage)
    dev_repo = SqliteDeviceRepository(storage)
    cred_store = ProtectedLocalCredentialStore(storage, master_key="TEST_DOC_KEY")

    dev_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)
    job_service = JobService(job_repo=job_repo, event_repo=event_repo, session_repo=session_repo)
    session_service = SessionService(session_repo=session_repo, event_repo=event_repo, device_service=dev_service)

    # Server with auth enabled to test that documentation is publicly accessible
    server = APIServer(
        session_service=session_service,
        job_service=job_service,
        device_service=dev_service,
        event_repo=event_repo,
        host="127.0.0.1",
        port=0,
        api_token="PROTECTED_TOKEN_ABC",
    )
    server.start_in_thread()
    time.sleep(0.1)

    yield server

    server.stop()
    session_service.close_all()
    storage.close()


def test_openapi_specification_endpoint(doc_api_server: APIServer) -> None:
    base = doc_api_server.base_url

    # GET /openapi.json without authorization header must succeed
    status, content_type, body = raw_http_get(f"{base}/openapi.json")
    assert status == 200
    assert "application/json" in content_type

    spec = json.loads(body)
    assert spec["openapi"] == "3.0.3"
    assert spec["info"]["title"] == "Terminal Session Manager API"
    assert spec["info"]["version"] == "0.1.0"

    # Verify security schemes are documented
    security_schemes = spec["components"]["securitySchemes"]
    assert "bearerAuth" in security_schemes
    assert "apiKeyAuth" in security_schemes

    # Verify key paths exist
    paths = spec["paths"]
    assert "/openapi.json" in paths
    assert "/docs" in paths
    assert "/sessions" in paths
    assert "/sessions/{id}" in paths
    assert "/sessions/{id}/write" in paths
    assert "/sessions/{id}/read" in paths
    assert "/sessions/{id}/events" in paths
    assert "/sessions/{id}/jobs" in paths
    assert "/jobs" in paths
    assert "/jobs/{id}" in paths
    assert "/jobs/{id}/wait" in paths
    assert "/jobs/{id}/cancel" in paths
    assert "/devices" in paths
    assert "/devices/{id_or_name}" in paths
    assert "/devices/{id_or_name}/resolve" in paths

    # Security check: Ensure secret or password fields are NOT in schema responses
    resolved_schema = spec["components"]["schemas"]["ResolvedConnection"]
    properties = resolved_schema["properties"]
    assert "has_credential" in properties
    assert "password" not in properties
    assert "secret" not in properties
    assert "private_key" not in properties


def test_swagger_ui_endpoint(doc_api_server: APIServer) -> None:
    base = doc_api_server.base_url

    # GET /docs without authorization header must succeed and return HTML
    status, content_type, html = raw_http_get(f"{base}/docs")
    assert status == 200
    assert "text/html" in content_type

    # Verify Swagger UI elements are present
    assert "swagger-ui" in html
    assert "SwaggerUIBundle" in html
    assert "/openapi.json" in html
    assert "<!DOCTYPE html>" in html
