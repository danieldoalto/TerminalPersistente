"""HTTP request handler implementing REST API for sessions, jobs, events, and devices."""

from __future__ import annotations

from datetime import datetime, timezone
import hmac
from http.server import BaseHTTPRequestHandler
import json
from typing import Any
import urllib.parse

from terminal_session_manager.api.openapi import get_openapi_spec, get_swagger_ui_html
from terminal_session_manager.errors import (

    CredentialNotFoundError,
    CredentialResolutionError,
    DeviceInactiveError,
    DeviceNotFoundError,
    DomainError,
    EntityNotFoundError,
    InvalidStateError,
    InvalidStateTransitionError,
    JobNotFoundError,
    SessionNotFoundError,
    TransportClosedError,
    TransportNotOpenError,
    TransportTimeoutError,
    ValidationError,
)
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.models.event import Event
from terminal_session_manager.models.job import Job
from terminal_session_manager.models.session import Session


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def session_to_dict(session: Session) -> dict[str, Any]:
    return {
        "id": session.id,
        "name": session.name,
        "status": session.status.value,
        "device_id": session.device_id,
        "created_at": _iso(session.created_at),
        "updated_at": _iso(session.updated_at),
        "closed_at": _iso(session.closed_at),
        "metadata": session.metadata,
    }


def job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "session_id": job.session_id,
        "command": job.command,
        "status": job.status.value,
        "device_id": job.device_id,
        "created_at": _iso(job.created_at),
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "exit_code": job.exit_code,
        "inputs": job.inputs,
        "stdout": job.stdout,
        "stderr": job.stderr,
        "failure_reason": job.failure_reason,
        "metadata": job.metadata,
    }


def event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "sequence": event.sequence,
        "session_id": event.session_id,
        "job_id": event.job_id,
        "event_type": event.event_type.value,
        "payload": event.payload,
        "timestamp": _iso(event.timestamp),
        "is_masked": event.is_masked,
        "metadata": event.metadata,
    }


def device_to_dict(device: Device) -> dict[str, Any]:
    return {
        "id": device.id,
        "name": device.name,
        "host": device.host,
        "port": device.port,
        "device_type": device.device_type.value,
        "connection_method": device.connection_method.value,
        "default_user": device.default_user,
        "options": device.options,
        "credential_ref_id": device.credential_ref_id,
        "is_active": device.is_active,
        "is_deleted": device.is_deleted,
        "created_at": _iso(device.created_at),
        "updated_at": _iso(device.updated_at),
    }


class TSMRequestHandler(BaseHTTPRequestHandler):
    """Processes HTTP API requests with token authentication and domain error translation."""

    server: Any  # Points to APIServer instance

    def log_message(self, format: str, *args: Any) -> None:
        """Suppresses default stderr server logging for quiet test execution."""
        pass

    def _check_auth(self) -> bool:
        """Verifies Bearer token or X-API-Key against server configured token."""
        api_token = getattr(self.server, "api_token", None)
        if not api_token:
            return True

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path in ("/openapi.json", "/docs", "/docs/"):
            return True

        auth_header = self.headers.get("Authorization", "")
        api_key_header = self.headers.get("X-API-Key", "")

        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif api_key_header:
            token = api_key_header.strip()

        if not token or not hmac.compare_digest(token.encode("utf-8"), api_token.encode("utf-8")):
            self._send_error(401, "Unauthorized", "Missing or invalid authorization token.")
            return False

        return True

    def _send_html(self, html: str, status: int = 200) -> None:
        """Sends HTML response body with appropriate headers."""
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Serializes and sends JSON response body with appropriate headers."""
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, status: int, error_code: str, message: str) -> None:
        """Sends standardized JSON error response without internal leakages."""
        self._send_json(
            {
                "error": error_code,
                "message": message,
                "status_code": status,
            },
            status=status,
        )

    def _read_json(self) -> dict[str, Any]:
        """Reads and parses JSON request payload safely."""
        content_length_header = self.headers.get("Content-Length")
        if not content_length_header:
            return {}

        try:
            length = int(content_length_header)
            if length > 10 * 1024 * 1024:  # 10MB safety limit
                raise ValidationError("Request payload exceeds maximum allowed size (10MB).")
            raw = self.rfile.read(length).decode("utf-8")
            if not raw.strip():
                return {}
            return json.loads(raw)
        except json.JSONDecodeError as err:
            raise ValidationError(f"Malformed JSON payload: {err}") from err

    def do_GET(self) -> None:
        """Handles HTTP GET requests."""
        if not self._check_auth():
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        try:
            # GET /openapi.json
            if path == "/openapi.json":
                self._send_json(get_openapi_spec())
                return

            # GET /docs
            if path in ("/docs", "/docs/"):
                self._send_html(get_swagger_ui_html())
                return

            # GET /sessions
            if path == "/sessions":
                sessions = self.server.session_service.list_sessions()
                self._send_json({"items": [session_to_dict(s) for s in sessions], "total": len(sessions)})
                return


            # GET /sessions/{id}
            parts = path.split("/")
            if len(parts) == 3 and parts[1] == "sessions":
                session_id = parts[2]
                session = self.server.session_service.get_session(session_id)
                self._send_json(session_to_dict(session))
                return

            # GET /sessions/{id}/events
            if len(parts) == 4 and parts[1] == "sessions" and parts[3] == "events":
                session_id = parts[2]
                since_seq = int(query.get("since_sequence", ["0"])[0])
                limit_str = query.get("limit", ["50"])[0]
                limit = min(int(limit_str), 200)

                events = self.server.event_repo.get_events(
                    session_id=session_id,
                    since_sequence=since_seq,
                    limit=limit,
                )
                latest_seq = -1
                if hasattr(self.server.event_repo, "get_latest_sequence"):
                    latest_seq = self.server.event_repo.get_latest_sequence(session_id)

                self._send_json(
                    {
                        "items": [event_to_dict(e) for e in events],
                        "count": len(events),
                        "since_sequence": since_seq,
                        "latest_sequence": latest_seq,
                    }
                )
                return

            # GET /sessions/{id}/jobs
            if len(parts) == 4 and parts[1] == "sessions" and parts[3] == "jobs":
                session_id = parts[2]
                jobs = self.server.job_service.list_jobs(session_id)
                self._send_json({"items": [job_to_dict(j) for j in jobs], "total": len(jobs)})
                return

            # GET /jobs/{id}
            if len(parts) == 3 and parts[1] == "jobs":
                job_id = parts[2]
                job = self.server.job_service.get_job(job_id)
                self._send_json(job_to_dict(job))
                return

            # GET /devices
            if path == "/devices":
                only_active_val = query.get("only_active", ["true"])[0].lower()
                only_active = only_active_val not in ("false", "0", "no")
                devices = self.server.device_service.list_devices(only_active=only_active)
                self._send_json({"items": [device_to_dict(d) for d in devices], "total": len(devices)})
                return

            # GET /devices/{id_or_name}/resolve (MUST NOT leak secret!)
            if len(parts) == 4 and parts[1] == "devices" and parts[3] == "resolve":
                target = parts[2]
                resolved = self.server.device_service.resolve_connection(target)
                self._send_json(
                    {
                        "device_id": resolved.device_id,
                        "device_name": resolved.device_name,
                        "host": resolved.host,
                        "port": resolved.port,
                        "connection_method": resolved.connection_method.value,
                        "default_user": resolved.default_user,
                        "has_credential": resolved.credential_ref is not None,
                        "credential_ref_id": resolved.credential_ref.id if resolved.credential_ref else None,
                        "options": resolved.options,
                    }
                )
                return

            # GET /devices/{id_or_name}
            if len(parts) == 3 and parts[1] == "devices":
                target = parts[2]
                device = self.server.device_service.get_device_by_name(target)
                if device is None:
                    device = self.server.device_service.get_device(target)
                if device is None:
                    raise DeviceNotFoundError(target)
                self._send_json(device_to_dict(device))
                return

            self._send_error(404, "RouteNotFound", f"GET route '{path}' does not exist.")
        except Exception as exc:
            self._handle_exception(exc)

    def do_POST(self) -> None:
        """Handles HTTP POST requests."""
        if not self._check_auth():
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = path.split("/")

        try:
            body = self._read_json()

            # POST /sessions
            if path == "/sessions":
                name = body.get("name", "default")
                device_identifier = body.get("device_identifier")
                metadata = body.get("metadata", {})
                local_session = self.server.session_service.create_session(
                    name=name,
                    device_identifier=device_identifier,
                    metadata=metadata,
                )
                self._send_json(session_to_dict(local_session.session), status=201)
                return

            # POST /sessions/{id}/write
            if len(parts) == 4 and parts[1] == "sessions" and parts[3] == "write":
                session_id = parts[2]
                data = body.get("data", "")
                is_sensitive = bool(body.get("is_sensitive", False))
                written = self.server.session_service.write_session(
                    session_id=session_id,
                    data=data,
                    is_sensitive=is_sensitive,
                )
                self._send_json({"session_id": session_id, "bytes_written": written})
                return

            # POST /sessions/{id}/read
            if len(parts) == 4 and parts[1] == "sessions" and parts[3] == "read":
                session_id = parts[2]
                max_bytes = int(body.get("max_bytes", 4096))
                timeout = float(body["timeout"]) if "timeout" in body and body["timeout"] is not None else None
                text = self.server.session_service.read_session(
                    session_id=session_id,
                    max_bytes=max_bytes,
                    timeout=timeout,
                )
                session = self.server.session_service.get_session(session_id)
                self._send_json({"session_id": session_id, "data": text, "status": session.status.value})
                return

            # POST /sessions/{id}/close
            if len(parts) == 4 and parts[1] == "sessions" and parts[3] == "close":
                session_id = parts[2]
                session = self.server.session_service.close_session(session_id)
                self._send_json(session_to_dict(session))
                return

            # POST /sessions/{id}/jobs or POST /jobs
            if (len(parts) == 4 and parts[1] == "sessions" and parts[3] == "jobs") or path == "/jobs":
                session_id = parts[2] if len(parts) == 4 else body.get("session_id")
                if not session_id:
                    raise ValidationError("Field 'session_id' is required to submit a job.")

                command = body.get("command")
                if not command:
                    raise ValidationError("Field 'command' is required to submit a job.")

                inputs = body.get("inputs")
                timeout_val = body.get("timeout") if "timeout" in body else body.get("timeout_seconds")
                metadata = body.get("metadata")

                job = self.server.job_service.submit_job(
                    session_id=session_id,
                    command=command,
                    inputs=inputs,
                    timeout=float(timeout_val) if timeout_val is not None else None,
                    metadata=metadata,
                )
                self._send_json(job_to_dict(job), status=202)
                return


            # POST /jobs/{id}/wait
            if len(parts) == 4 and parts[1] == "jobs" and parts[3] == "wait":
                job_id = parts[2]
                timeout = float(body.get("timeout", 10.0))
                job = self.server.job_service.wait_job(job_id=job_id, timeout=timeout)
                self._send_json(job_to_dict(job))
                return

            # POST /jobs/{id}/cancel
            if len(parts) == 4 and parts[1] == "jobs" and parts[3] == "cancel":
                job_id = parts[2]
                job = self.server.job_service.cancel_job(job_id=job_id)
                self._send_json(job_to_dict(job))
                return

            # POST /devices
            if path == "/devices":
                name = body.get("name")
                host = body.get("host")
                if not name or not host:
                    raise ValidationError("Fields 'name' and 'host' are required to create a device.")

                port = int(body.get("port", 22))
                device_type = DeviceType(body.get("device_type", DeviceType.SERVER.value))
                conn_method = ConnectionMethod(body.get("connection_method", ConnectionMethod.SSH.value))
                default_user = body.get("default_user")
                options = body.get("options", {})
                credential_ref_id = body.get("credential_ref_id")

                device = self.server.device_service.create_device(
                    name=name,
                    host=host,
                    port=port,
                    device_type=device_type,
                    connection_method=conn_method,
                    default_user=default_user,
                    options=options,
                    credential_ref_id=credential_ref_id,
                )
                self._send_json(device_to_dict(device), status=201)
                return

            # POST /devices/{id}/deactivate
            if len(parts) == 4 and parts[1] == "devices" and parts[3] == "deactivate":
                device_id = parts[2]
                device = self.server.device_service.deactivate_device(device_id)
                self._send_json(device_to_dict(device))
                return

            self._send_error(404, "RouteNotFound", f"POST route '{path}' does not exist.")
        except Exception as exc:
            self._handle_exception(exc)

    def do_PATCH(self) -> None:
        """Handles HTTP PATCH requests (device updates)."""
        self._handle_update()

    def do_PUT(self) -> None:
        """Handles HTTP PUT requests (device updates)."""
        self._handle_update()

    def _handle_update(self) -> None:
        if not self._check_auth():
            return

        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.rstrip("/").split("/")

        try:
            body = self._read_json()
            # PATCH/PUT /devices/{id}
            if len(parts) == 3 and parts[1] == "devices":
                device_id = parts[2]
                updated = self.server.device_service.update_device(
                    device_id=device_id,
                    name=body.get("name"),
                    host=body.get("host"),
                    port=int(body["port"]) if "port" in body and body["port"] is not None else None,
                    device_type=DeviceType(body["device_type"]) if "device_type" in body and body["device_type"] is not None else None,
                    connection_method=ConnectionMethod(body["connection_method"]) if "connection_method" in body and body["connection_method"] is not None else None,
                    default_user=body.get("default_user"),
                    options=body.get("options"),
                    credential_ref_id=body.get("credential_ref_id"),
                    is_active=body.get("is_active"),
                )
                self._send_json(device_to_dict(updated))
                return

            self._send_error(404, "RouteNotFound", f"Update route '{parsed.path}' does not exist.")
        except Exception as exc:
            self._handle_exception(exc)

    def do_DELETE(self) -> None:
        """Handles HTTP DELETE requests."""
        if not self._check_auth():
            return

        parsed = urllib.parse.urlparse(self.path)
        parts = parsed.path.rstrip("/").split("/")

        try:
            # DELETE /sessions/{id}
            if len(parts) == 3 and parts[1] == "sessions":
                session_id = parts[2]
                session = self.server.session_service.close_session(session_id)
                self._send_json(session_to_dict(session))
                return

            # DELETE /devices/{id}
            if len(parts) == 3 and parts[1] == "devices":
                device_id = parts[2]
                device = self.server.device_service.remove_device(device_id)
                self._send_json(device_to_dict(device))
                return

            self._send_error(404, "RouteNotFound", f"DELETE route '{parsed.path}' does not exist.")
        except Exception as exc:
            self._handle_exception(exc)

    def _handle_exception(self, exc: Exception) -> None:
        """Maps domain exceptions to HTTP status codes with sanitization."""
        if isinstance(exc, EntityNotFoundError):
            self._send_error(404, type(exc).__name__, str(exc))
        elif isinstance(exc, (ValidationError, InvalidStateTransitionError, InvalidStateError, DeviceInactiveError)):
            self._send_error(400, type(exc).__name__, str(exc))
        elif isinstance(exc, (TransportClosedError, TransportNotOpenError)):
            self._send_error(409, type(exc).__name__, str(exc))
        elif isinstance(exc, TransportTimeoutError):
            self._send_error(504, type(exc).__name__, str(exc))
        elif isinstance(exc, CredentialResolutionError):
            self._send_error(500, "CredentialResolutionError", "Failed to resolve credentials safely.")
        else:
            self._send_error(500, "InternalServerError", "An unexpected internal server error occurred.")
