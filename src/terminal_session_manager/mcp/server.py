"""FastMCP server implementation exposing Terminal Session Manager tools."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Union

from fastmcp import FastMCP

from terminal_session_manager.api.handler import (
    device_to_dict,
    event_to_dict,
    job_to_dict,
    session_to_dict,
)
from terminal_session_manager.config import TSMConfig, load_config
from terminal_session_manager.errors import DeviceNotFoundError, DomainError, JobNotFoundError
from terminal_session_manager.interfaces.persistence import EventRepository
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


def create_mcp_server(
    session_service: SessionService | None = None,
    job_service: JobService | None = None,
    device_service: DeviceService | None = None,
    event_repo: EventRepository | None = None,
    storage: SqliteStorage | None = None,
    db_path: str | None = None,
    config: TSMConfig | None = None,
    name: str = "TerminalSessionManager",
) -> FastMCP:
    """Creates a configured FastMCP server exposing TSM capabilities to agents."""
    if storage is None and (session_service is None or job_service is None or device_service is None or event_repo is None):
        cfg = config if config is not None else load_config()
        if db_path is None:
            db_path = cfg.storage.db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        storage = SqliteStorage(db_path)

    if event_repo is None and storage is not None:
        event_repo = SqliteEventRepository(storage)

    if device_service is None and storage is not None:
        dev_repo = SqliteDeviceRepository(storage)
        master_key = config.security.master_key if config is not None else None
        cred_store = ProtectedLocalCredentialStore(storage, master_key=master_key)
        device_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)

    if job_service is None and storage is not None and event_repo is not None:
        job_repo = SqliteJobRepository(storage)
        session_repo = SqliteSessionRepository(storage)
        job_service = JobService(job_repo=job_repo, event_repo=event_repo, session_repo=session_repo)

    if session_service is None and storage is not None and event_repo is not None:
        session_repo = SqliteSessionRepository(storage)
        session_service = SessionService(session_repo=session_repo, event_repo=event_repo, device_service=device_service)

    assert session_service is not None
    assert job_service is not None
    assert device_service is not None
    assert event_repo is not None

    mcp = FastMCP(name=name)

    # -------------------------------------------------------------------------
    # Session Management Tools
    # -------------------------------------------------------------------------

    @mcp.tool
    def create_session(
        name: str = "default",
        device_identifier: str | None = None,
    ) -> dict[str, Any]:
        """Creates and starts a new persistent terminal session.

        Args:
            name: Human-readable name for the session.
            device_identifier: Optional nickname or UUID of a registered device to bind.
        """
        try:
            local_session = session_service.create_session(
                name=name,
                device_identifier=device_identifier,
            )
            return session_to_dict(local_session.session)
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def get_session(session_id: str) -> dict[str, Any]:
        """Retrieves session metadata and live status by session ID."""
        try:
            session = session_service.get_session(session_id)
            return session_to_dict(session)
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def list_sessions() -> list[dict[str, Any]]:
        """Lists all registered sessions with up-to-date execution status."""
        try:
            sessions = session_service.list_sessions()
            return [session_to_dict(s) for s in sessions]
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def write_session(
        session_id: str,
        data: str,
        is_sensitive: bool = False,
    ) -> dict[str, Any]:
        """Writes input data to an active terminal session.

        Args:
            session_id: ID of the active session.
            data: Command or input string to send.
            is_sensitive: If True, masks the input as [REDACTED] in recorded history.
        """
        try:
            written = session_service.write_session(
                session_id=session_id,
                data=data,
                is_sensitive=is_sensitive,
            )
            return {"session_id": session_id, "bytes_written": written}
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def read_session(
        session_id: str,
        max_bytes: int = 4096,
        timeout: float = 0.5,
    ) -> dict[str, Any]:
        """Reads output text from an active terminal session.

        Sensitive tokens and credentials are automatically redacted before returning.
        """
        try:
            text = session_service.read_session(
                session_id=session_id,
                max_bytes=max_bytes,
                timeout=timeout,
            )
            session = session_service.get_session(session_id)
            return {
                "session_id": session_id,
                "data": text,
                "status": session.status.value,
            }
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def close_session(session_id: str) -> dict[str, Any]:
        """Terminates an active session and marks it closed."""
        try:
            session = session_service.close_session(session_id)
            return session_to_dict(session)
        except DomainError as err:
            raise ValueError(str(err)) from err

    # -------------------------------------------------------------------------
    # Event History Tools
    # -------------------------------------------------------------------------

    @mcp.tool
    def get_events(
        session_id: str,
        since_sequence: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Retrieves ordered event stream for a session using cursor pagination.

        Args:
            session_id: Session identifier.
            since_sequence: Starting sequence number (inclusive cursor).
            limit: Maximum events to return (capped at 200).
        """
        try:
            capped_limit = min(max(1, limit), 200)
            events = event_repo.get_events(
                session_id=session_id,
                since_sequence=since_sequence,
                limit=capped_limit,
            )
            latest_seq = -1
            if hasattr(event_repo, "get_latest_sequence"):
                latest_seq = event_repo.get_latest_sequence(session_id)

            return {
                "items": [event_to_dict(e) for e in events],
                "count": len(events),
                "since_sequence": since_sequence,
                "latest_sequence": latest_seq,
            }
        except DomainError as err:
            raise ValueError(str(err)) from err

    # -------------------------------------------------------------------------
    # Asynchronous Job Execution Tools
    # -------------------------------------------------------------------------

    @mcp.tool
    def submit_job(
        session_id: str,
        command: Union[list[str], str],
        inputs: list[str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Submits an asynchronous command to execute in background within a session.

        Args:
            session_id: The ID of the session the job runs in.
            command: The command to execute (as a list of arguments or a shell string).
            inputs: Optional stdin lines to send.
            timeout: Maximum execution duration in seconds.
        """
        try:
            job = job_service.submit_job(
                session_id=session_id,
                command=command,
                inputs=inputs,
                timeout=timeout,
            )
            return job_to_dict(job)
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def get_job(job_id: str) -> dict[str, Any]:
        """Queries the execution status, exit code, and outputs of a background job."""
        try:
            job = job_service.get_job(job_id)
            if job is None:
                raise JobNotFoundError(job_id)
            return job_to_dict(job)
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def list_jobs(session_id: str) -> list[dict[str, Any]]:
        """Lists all background jobs associated with a specific session."""
        try:
            jobs = job_service.list_jobs(session_id)
            return [job_to_dict(j) for j in jobs]
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def wait_job(job_id: str, timeout: float = 10.0) -> dict[str, Any]:
        """Blocks until a job completes, fails, or exceeds the specified timeout."""
        try:
            job = job_service.wait_job(job_id=job_id, timeout=timeout)
            return job_to_dict(job)
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def cancel_job(job_id: str) -> dict[str, Any]:
        """Cancels a running background job, terminating its process."""
        try:
            job = job_service.cancel_job(job_id=job_id)
            return job_to_dict(job)
        except DomainError as err:
            raise ValueError(str(err)) from err

    # -------------------------------------------------------------------------
    # Device Inventory and Resolution Tools
    # -------------------------------------------------------------------------

    @mcp.tool
    def list_devices(only_active: bool = True) -> list[dict[str, Any]]:
        """Lists registered devices in inventory without secrets."""
        try:
            devices = device_service.list_devices(only_active=only_active)
            return [device_to_dict(d) for d in devices]
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def get_device(name_or_id: str) -> dict[str, Any]:
        """Retrieves non-sensitive device configuration by nickname or ID."""
        try:
            device = device_service.get_device_by_name(name_or_id)
            if device is None:
                device = device_service.get_device(name_or_id)
            if device is None:
                raise DeviceNotFoundError(name_or_id)
            return device_to_dict(device)
        except DomainError as err:
            raise ValueError(str(err)) from err

    @mcp.tool
    def resolve_device(name_or_id: str) -> dict[str, Any]:
        """Resolves device connection details internally by nickname.

        NOTE: Strictly omits secrets, passwords, or keys from the output.
        Confirms connectivity parameters and indicates if a credential was resolved.
        """
        try:
            resolved = device_service.resolve_connection(name_or_id)
            return {
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
        except DomainError as err:
            raise ValueError(str(err)) from err

    return mcp


def main() -> None:
    """CLI entrypoint for running the FastMCP server via stdio transport."""
    from terminal_session_manager.app import TSMApplication

    app = TSMApplication()
    app.startup()
    server = app.create_mcp_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
