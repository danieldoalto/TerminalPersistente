"""Local session controller binding Session lifecycle to TerminalTransport and persistence."""

from __future__ import annotations

from typing import Any

from terminal_session_manager.config import SSHConfig
from terminal_session_manager.errors import TransportClosedError, TransportError
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    SessionRepository,
)
from terminal_session_manager.interfaces.transport import TerminalTransport
from terminal_session_manager.models.credential import CredentialType
from terminal_session_manager.models.device import ConnectionMethod
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.session import Session, SessionStatus
from terminal_session_manager.services.device_service import (
    DeviceService,
    ResolvedConnection,
)
from terminal_session_manager.transports.local_process import LocalProcessTransport
from terminal_session_manager.transports.ssh import SSHTransport


class LocalSession:
    """Orchestrates an interactive local or remote terminal session.

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
        device_service: DeviceService | None = None,
        device_identifier: str | None = None,
        resolved_connection: ResolvedConnection | None = None,
        sensitive_tokens: list[str | bytes] | None = None,
        ssh_config: SSHConfig | None = None,
    ) -> None:
        self.session = session or Session()
        self.session_repo = session_repo
        self.event_repo = event_repo
        self.encoding = encoding
        self.device_service = device_service
        self.resolved_connection = resolved_connection
        self.ssh_config = ssh_config

        # Resolve device if identifier and service are provided
        if self.resolved_connection is None and self.device_service and device_identifier:
            self.resolved_connection = self.device_service.resolve_connection(device_identifier)

        if self.resolved_connection is not None:
            self.session.device_id = self.resolved_connection.device_id

        # Determine transport: injected, SSH, or LocalProcess
        if transport is not None:
            self.transport = transport
        elif self.resolved_connection and self.resolved_connection.connection_method == ConnectionMethod.SSH:
            cred_type = (
                self.resolved_connection.credential_ref.credential_type
                if self.resolved_connection.credential_ref
                else None
            )
            password = None
            private_key = None
            secret = self.resolved_connection.secret
            if cred_type == CredentialType.PASSWORD:
                password = secret if isinstance(secret, str) else (secret.decode("utf-8", errors="ignore") if secret else None)
            elif cred_type == CredentialType.SSH_KEY:
                private_key = secret
            elif secret:
                sec_str = secret if isinstance(secret, str) else secret.decode("utf-8", errors="ignore")
                if "PRIVATE KEY" in sec_str:
                    private_key = secret
                else:
                    password = sec_str

            known_hosts = self.ssh_config.known_hosts_path if self.ssh_config else None
            strict_checking = self.ssh_config.strict_host_key_checking if self.ssh_config else True
            timeout = self.ssh_config.connect_timeout if self.ssh_config else 10.0

            opts = self.resolved_connection.options
            if "known_hosts_path" in opts:
                known_hosts = opts["known_hosts_path"]
            if "strict_host_key_checking" in opts:
                strict_checking = bool(opts["strict_host_key_checking"])
            if "connect_timeout" in opts:
                timeout = float(opts["connect_timeout"])

            self.transport = SSHTransport(
                host=self.resolved_connection.host,
                port=self.resolved_connection.port,
                username=self.resolved_connection.default_user,
                password=password,
                private_key=private_key,
                known_hosts_path=known_hosts,
                strict_host_key_checking=strict_checking,
                connect_timeout=timeout,
                options=opts,
            )
        else:
            self.transport = LocalProcessTransport()

        # Internal sensitive token tracking for output/input redaction
        self._sensitive_tokens: list[str] = []
        if self.resolved_connection and self.resolved_connection.secret:
            sec = self.resolved_connection.secret
            sec_str = sec if isinstance(sec, str) else sec.decode(self.encoding, errors="ignore")
            if sec_str:
                self._sensitive_tokens.append(sec_str)

        if sensitive_tokens:
            for tok in sensitive_tokens:
                tok_str = tok if isinstance(tok, str) else tok.decode(self.encoding, errors="ignore")
                if tok_str:
                    self._sensitive_tokens.append(tok_str)

        # Determine starting sequence number for events
        self._sequence = 0
        if self.event_repo is not None and hasattr(self.event_repo, "get_latest_sequence"):
            latest = self.event_repo.get_latest_sequence(self.session.id)
            if latest >= 0:
                self._sequence = latest + 1

        # Initial persistence if repo provided
        if self.session_repo is not None:
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

    def _mask_text(self, text: str) -> tuple[str, bool]:
        """Scans and redacts configured sensitive tokens from text."""
        is_masked = False
        result = text
        for token in self._sensitive_tokens:
            if token and token in result:
                result = result.replace(token, "[REDACTED]")
                is_masked = True
        return result, is_masked

    def write(self, data: bytes | str, is_sensitive: bool = False) -> int:
        """Writes data to the session transport channel and records STDIN event."""
        self.poll_status()
        if self.session.status != SessionStatus.RUNNING:
            raise TransportClosedError(
                f"Cannot write: session is not running (status: {self.session.status.value})."
            )

        raw_bytes = data.encode(self.encoding) if isinstance(data, str) else data
        written = self.transport.write(raw_bytes)

        text = (
            data
            if isinstance(data, str)
            else data.decode(self.encoding, errors="replace")
        )
        masked_text, had_mask = self._mask_text(text)

        if is_sensitive:
            self._record_event(
                EventType.STDIN,
                payload="[REDACTED]",
                is_masked=True,
            )
        elif had_mask:
            self._record_event(
                EventType.STDIN,
                payload=masked_text,
                is_masked=True,
            )
        else:
            self._record_event(EventType.STDIN, payload=text, is_masked=False)

        return written

    def read(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        """Reads raw bytes from the session transport channel and records STDOUT event."""
        data = self.transport.read(max_bytes=max_bytes, timeout=timeout)
        if data:
            text = data.decode(self.encoding, errors="replace")
            masked_text, is_masked = self._mask_text(text)
            self._record_event(EventType.STDOUT, payload=masked_text, is_masked=is_masked)

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
