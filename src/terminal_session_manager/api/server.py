"""HTTP server management for Terminal Session Manager."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
import threading
from typing import Any

from terminal_session_manager.api.handler import TSMRequestHandler
from terminal_session_manager.interfaces.persistence import EventRepository
from terminal_session_manager.services.device_service import DeviceService
from terminal_session_manager.services.job_service import JobService
from terminal_session_manager.services.session_service import SessionService


class APIServer:
    """Encapsulates the standard library ThreadingHTTPServer lifecycle for TSM."""

    def __init__(
        self,
        session_service: SessionService,
        job_service: JobService,
        device_service: DeviceService,
        event_repo: EventRepository,
        host: str = "127.0.0.1",
        port: int = 0,
        api_token: str | None = None,
        config: Any | None = None,
    ) -> None:
        self.session_service = session_service
        self.job_service = job_service
        self.device_service = device_service
        self.event_repo = event_repo
        self.config = config

        if config is not None:
            if host == "127.0.0.1" and hasattr(config, "server"):
                host = config.server.host
            if port == 0 and hasattr(config, "server"):
                port = config.server.port
            if api_token is None and hasattr(config, "server"):
                api_token = config.server.api_token

        self.api_token = api_token

        # Create threading HTTP server on requested host and port
        self._server = ThreadingHTTPServer((host, port), TSMRequestHandler)
        # Bind references directly to the server object so handler instances can access them
        self._server.session_service = self.session_service  # type: ignore[attr-defined]
        self._server.job_service = self.job_service  # type: ignore[attr-defined]
        self._server.device_service = self.device_service  # type: ignore[attr-defined]
        self._server.event_repo = self.event_repo  # type: ignore[attr-defined]
        self._server.api_token = self.api_token  # type: ignore[attr-defined]

        self._thread: threading.Thread | None = None
        self._is_running = False

    @property
    def host(self) -> str:
        """Returns the bound host address."""
        return str(self._server.server_address[0])

    @property
    def port(self) -> int:
        """Returns the actual bound TCP port number."""
        return int(self._server.server_address[1])

    @property
    def base_url(self) -> str:
        """Returns base HTTP URL (e.g. http://127.0.0.1:54321)."""
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        """Starts serving requests synchronously (blocking)."""
        self._is_running = True
        try:
            self._server.serve_forever()
        finally:
            self._is_running = False

    def start_in_thread(self) -> threading.Thread:
        """Starts server in a background daemon thread for testing or concurrent execution."""
        if self._thread is not None and self._thread.is_alive():
            return self._thread

        self._is_running = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        """Stops server and releases socket cleanly."""
        if self._is_running:
            self._server.shutdown()
            self._server.server_close()
            self._is_running = False
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=3.0)
                self._thread = None
