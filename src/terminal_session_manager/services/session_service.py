"""Session lifecycle and interactive I/O coordinator service."""

from __future__ import annotations

import threading
from typing import Any

from terminal_session_manager.errors import (
    SessionNotFoundError,
    TransportClosedError,
)
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    SessionRepository,
)
from terminal_session_manager.interfaces.transport import TerminalTransport
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.session import Session, SessionStatus
from terminal_session_manager.services.device_service import DeviceService
from terminal_session_manager.services.local_session import LocalSession


class SessionService:
    """Coordinates interactive terminal sessions, persistence, and active processes."""

    def __init__(
        self,
        session_repo: SessionRepository,
        event_repo: EventRepository,
        device_service: DeviceService | None = None,
    ) -> None:
        self.session_repo = session_repo
        self.event_repo = event_repo
        self.device_service = device_service
        self._active_sessions: dict[str, LocalSession] = {}
        self._lock = threading.RLock()

    def create_session(
        self,
        name: str = "default",
        device_identifier: str | None = None,
        metadata: dict[str, Any] | None = None,
        transport: TerminalTransport | None = None,
        auto_start: bool = True,
    ) -> LocalSession:
        """Creates, optionally starts, and registers a new interactive session."""
        session = Session(name=name, metadata=metadata or {})

        local_session = LocalSession(
            session=session,
            transport=transport,
            session_repo=self.session_repo,
            event_repo=self.event_repo,
            device_service=self.device_service,
            device_identifier=device_identifier,
        )

        if auto_start:
            local_session.start()

        with self._lock:
            self._active_sessions[session.id] = local_session

        return local_session

    def get_session(self, session_id: str) -> Session:
        """Retrieves session metadata, synchronizing status if currently active."""
        with self._lock:
            active = self._active_sessions.get(session_id)
            if active is not None:
                active.poll_status()

        session = self.session_repo.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    def get_active_session(self, session_id: str) -> LocalSession | None:
        """Returns the in-memory active LocalSession if open, else None."""
        with self._lock:
            return self._active_sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        """Lists all persisted sessions, updating status for active ones."""
        with self._lock:
            for active in self._active_sessions.values():
                active.poll_status()

        return self.session_repo.list_all()

    def write_session(
        self,
        session_id: str,
        data: str | bytes,
        is_sensitive: bool = False,
    ) -> int:
        """Writes data into an active session channel."""
        with self._lock:
            active = self._active_sessions.get(session_id)

        if active is None:
            session = self.session_repo.get_by_id(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            raise TransportClosedError(
                f"Session '{session_id}' is closed or not currently active (status: {session.status.value})."
            )

        return active.write(data, is_sensitive=is_sensitive)

    def read_session(
        self,
        session_id: str,
        max_bytes: int = 4096,
        timeout: float | None = None,
    ) -> str:
        """Reads decoded text from an active session channel with automatic masking."""
        with self._lock:
            active = self._active_sessions.get(session_id)

        if active is None:
            session = self.session_repo.get_by_id(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            raise TransportClosedError(
                f"Session '{session_id}' is closed or not currently active (status: {session.status.value})."
            )

        return active.read_text(max_bytes=max_bytes, timeout=timeout)

    def close_session(self, session_id: str) -> Session:
        """Terminates an active session and updates its final status."""
        with self._lock:
            active = self._active_sessions.pop(session_id, None)

        if active is not None:
            active.close()
            return active.session

        session = self.session_repo.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        return session

    def close_all(self) -> None:
        """Terminates all active sessions during shutdown."""
        with self._lock:
            sessions = list(self._active_sessions.values())
            self._active_sessions.clear()

        for active in sessions:
            try:
                active.close()
            except Exception:
                pass

    def recover_orphaned_sessions(self) -> int:
        """Reconciles interrupted sessions upon service restart.

        Scans repository for sessions in RUNNING or WAITING status that have
        no active transport process in memory and marks them as LOST.

        Returns:
            Number of recovered orphaned sessions.
        """
        recovered_count = 0
        persisted_sessions = self.session_repo.list_all()

        with self._lock:
            active_ids = set(self._active_sessions.keys())

        for session in persisted_sessions:
            if session.id not in active_ids and session.status in (
                SessionStatus.RUNNING,
                SessionStatus.WAITING,
                SessionStatus.CREATED,
            ):
                try:
                    session.transition_to(SessionStatus.LOST)
                    self.session_repo.save(session)
                    latest_seq = 0
                    if hasattr(self.event_repo, "get_latest_sequence"):
                        latest_seq = self.event_repo.get_latest_sequence(session.id)
                    event = Event(
                        session_id=session.id,
                        sequence=latest_seq + 1,
                        event_type=EventType.STATE_CHANGE,
                        payload={
                            "status": SessionStatus.LOST.value,
                            "reason": "Session orphaned across service restart; marked as LOST.",
                        },
                    )
                    self.event_repo.append(event)
                    recovered_count += 1
                except Exception:
                    pass

        return recovered_count
