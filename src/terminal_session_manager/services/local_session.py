"""Local session controller binding Session lifecycle to TerminalTransport and persistence."""

from __future__ import annotations

from typing import Any

from terminal_session_manager.errors import TransportClosedError, TransportError
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    SessionRepository,
)
from terminal_session_manager.interfaces.transport import TerminalTransport
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.session import Session, SessionStatus
from terminal_session_manager.transports.local_process import LocalProcessTransport


class LocalSession:
    """Orchestrates an interactive local terminal session.

    Connects the high-level Session entity lifecycle to an underlying
    TerminalTransport. Supports optional persistence of session metadata and
    ordered event history (inputs, outputs, errors, state transitions).
    """

    def __init__(
        self,
        session: Session | None = None,
        transport: TerminalTransport | None = None,
        session_repo: SessionRepository | None = None,
        event_repo: EventRepository | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self.session = session or Session()
        self.transport = transport or LocalProcessTransport()
        self.session_repo = session_repo
        self.event_repo = event_repo
        self.encoding = encoding

        # Determine starting sequence number for events
        self._sequence = 0
        if self.event_repo is not None and hasattr(self.event_repo, "get_latest_sequence"):
            latest = self.event_repo.get_latest_sequence(self.session.id)
            if latest >= 0:
                self._sequence = latest + 1

        # Initial persistence if repo provided
        if self.session_repo is not None and self.session_repo.get_by_id(self.session.id) is None:
            self._persist_session()

    @property
    def id(self) -> str:
        """Returns the session identifier."""
        return self.session.id

    @property
    def status(self) -> SessionStatus:
        """Returns current session status synchronized with the transport."""
        return self.poll_status()

    def _persist_session(self) -> None:
        if self.session_repo is not None:
            self.session_repo.save(self.session)

    def _record_event(
        self,
        event_type: EventType,
        payload: Any,
        is_masked: bool = False,
        job_id: str | None = None,
    ) -> None:
        if self.event_repo is not None:
            event = Event(
                sequence=self._sequence,
                session_id=self.session.id,
                job_id=job_id,
                event_type=event_type,
                payload=payload,
                is_masked=is_masked,
            )
            self.event_repo.append(event)
            self._sequence += 1

    def start(self) -> None:
        """Opens the transport and transitions session to RUNNING state.

        If transport initialization fails, the session transitions to FAILED.
        """
        if self.session.status != SessionStatus.CREATED:
            raise TransportError(
                f"Cannot start session from status '{self.session.status.value}'."
            )

        try:
            self.transport.open()
            self.session.transition_to(SessionStatus.RUNNING)
            self._persist_session()
            self._record_event(
                EventType.STATE_CHANGE,
                payload={"status": SessionStatus.RUNNING.value},
            )
        except Exception as err:
            if self.session.status == SessionStatus.CREATED:
                self.session.transition_to(SessionStatus.FAILED)
            self.session.metadata["start_error"] = str(err)
            self._persist_session()
            self._record_event(
                EventType.STATE_CHANGE,
                payload={"status": SessionStatus.FAILED.value, "error": str(err)},
            )
            raise

    def write(self, data: bytes | str, is_sensitive: bool = False) -> int:
        """Writes data to the session transport channel and records STDIN event."""
        self.poll_status()
        if self.session.status != SessionStatus.RUNNING:
            raise TransportClosedError(
                f"Cannot write: session is not running (status: {self.session.status.value})."
            )

        raw_bytes = data.encode(self.encoding) if isinstance(data, str) else data
        written = self.transport.write(raw_bytes)

        if is_sensitive:
            self._record_event(
                EventType.STDIN,
                payload="[REDACTED]",
                is_masked=True,
            )
        else:
            text = (
                data
                if isinstance(data, str)
                else data.decode(self.encoding, errors="replace")
            )
            self._record_event(EventType.STDIN, payload=text, is_masked=False)

        return written

    def read(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        """Reads raw bytes from the session transport channel and records STDOUT event."""
        data = self.transport.read(max_bytes=max_bytes, timeout=timeout)
        if data:
            text = data.decode(self.encoding, errors="replace")
            self._record_event(EventType.STDOUT, payload=text, is_masked=False)

        self.poll_status()
        return data

    def read_text(self, max_bytes: int = 4096, timeout: float | None = None) -> str:
        """Convenience method to read decoded text from the session."""
        raw = self.read(max_bytes=max_bytes, timeout=timeout)
        return raw.decode(self.encoding, errors="replace")

    def resize(self, rows: int, cols: int) -> None:
        """Resizes the terminal window dimensions."""
        self.transport.resize(rows=rows, cols=cols)

    def close(self) -> None:
        """Terminates transport cleanly and transitions session to CLOSED state."""
        try:
            self.transport.close()
        finally:
            if not self.session.is_terminal():
                self.session.transition_to(SessionStatus.CLOSED)
                self._persist_session()
                self._record_event(
                    EventType.STATE_CHANGE,
                    payload={"status": SessionStatus.CLOSED.value},
                )

    def poll_status(self) -> SessionStatus:
        """Inspects transport liveness and synchronizes session state."""
        if self.session.status == SessionStatus.RUNNING and not self.transport.is_alive():
            exit_code = getattr(self.transport, "exit_code", None)
            if exit_code is not None and exit_code != 0:
                self.session.transition_to(SessionStatus.FAILED)
                self.session.metadata["exit_code"] = exit_code
                self._persist_session()
                self._record_event(
                    EventType.STATE_CHANGE,
                    payload={"status": SessionStatus.FAILED.value, "exit_code": exit_code},
                )
            else:
                self.session.transition_to(SessionStatus.COMPLETED)
                if exit_code is not None:
                    self.session.metadata["exit_code"] = exit_code
                self._persist_session()
                self._record_event(
                    EventType.STATE_CHANGE,
                    payload={"status": SessionStatus.COMPLETED.value, "exit_code": exit_code},
                )

        return self.session.status
