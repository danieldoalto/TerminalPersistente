"""Central application container managing TSM services, storage, and lifecycle."""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Any

from terminal_session_manager.api.server import APIServer
from terminal_session_manager.config import TSMConfig, load_config
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


def _restrict_permissions(path: Path) -> None:
    """Applies restrictive file system permissions on POSIX systems."""
    if os.name != "nt":
        try:
            if path.is_dir():
                os.chmod(path, 0o700)
            elif path.is_file():
                os.chmod(path, 0o600)
        except OSError:
            pass


class TSMApplication:
    """Root application container unifying configuration, services, and lifecycle."""

    def __init__(self, config: TSMConfig | None = None) -> None:
        self.config = config if config is not None else load_config()

        # 1. Initialize persistent storage with secure directory permissions
        db_path = Path(self.config.storage.db_path)
        if self.config.storage.db_path != ":memory:":
            db_path.parent.mkdir(parents=True, exist_ok=True)
            _restrict_permissions(db_path.parent)

        self.storage = SqliteStorage(self.config.storage.db_path)
        if self.config.storage.db_path != ":memory:" and db_path.is_file():
            _restrict_permissions(db_path)

        # 2. Credential store & device service
        self.credential_store = ProtectedLocalCredentialStore(
            storage=self.storage,
            master_key=self.config.security.master_key,
        )
        self.device_repo = SqliteDeviceRepository(self.storage)
        self.device_service = DeviceService(
            repository=self.device_repo,
            credential_resolver=self.credential_store,
        )

        # 3. Session & event persistence and coordination
        self.event_repo = SqliteEventRepository(self.storage)
        self.session_repo = SqliteSessionRepository(self.storage)
        self.session_service = SessionService(
            session_repo=self.session_repo,
            event_repo=self.event_repo,
            device_service=self.device_service,
        )

        # 4. Job repository and execution service
        self.job_repo = SqliteJobRepository(self.storage)
        self.job_service = JobService(
            job_repo=self.job_repo,
            event_repo=self.event_repo,
            session_repo=self.session_repo,
        )

        self._is_started = False

    def startup(self) -> dict[str, int]:
        """Runs startup initialization, reconciling orphaned sessions and jobs."""
        recovered_jobs = 0
        recovered_sessions = 0

        if self.config.jobs.recover_orphaned_on_start:
            recovered_jobs = self.job_service.recover_orphaned_jobs()
            recovered_sessions = self.session_service.recover_orphaned_sessions()

        self._is_started = True
        return {
            "recovered_jobs": recovered_jobs,
            "recovered_sessions": recovered_sessions,
        }

    def shutdown(self) -> None:
        """Executes graceful shutdown: closes active sessions, terminates jobs, closes DB."""
        if self.config.sessions.cleanup_on_shutdown:
            self.session_service.close_all()

        # Stop any running job processes
        with self.job_service._lock:
            active_pids = list(self.job_service._active_processes.keys())
        for job_id in active_pids:
            try:
                self.job_service.cancel_job(job_id, reason="Application shutdown")
            except Exception:
                pass

        self.storage.close()
        self._is_started = False

    def create_api_server(self) -> APIServer:
        """Instantiates the HTTP API server bound to configured host, port, and token."""
        return APIServer(
            session_service=self.session_service,
            job_service=self.job_service,
            device_service=self.device_service,
            event_repo=self.event_repo,
            host=self.config.server.host,
            port=self.config.server.port,
            api_token=self.config.server.api_token,
        )

    def create_mcp_server(self, name: str = "TerminalSessionManager") -> Any:
        """Instantiates the FastMCP server with configured services and storage."""
        from terminal_session_manager.mcp.server import create_mcp_server

        return create_mcp_server(
            session_service=self.session_service,
            job_service=self.job_service,
            device_service=self.device_service,
            event_repo=self.event_repo,
            storage=self.storage,
            config=self.config,
            name=name,
        )
