"""Session domain model and state definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
import uuid

from terminal_session_manager.errors import InvalidStateTransitionError, ValidationError


class SessionStatus(str, Enum):
    """Conceptual states of a session."""

    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CLOSED = "closed"
    LOST = "lost"


# Allowed state transitions for sessions
SESSION_TRANSITIONS: dict[SessionStatus, set[SessionStatus]] = {
    SessionStatus.CREATED: {
        SessionStatus.RUNNING,
        SessionStatus.FAILED,
        SessionStatus.CLOSED,
    },
    SessionStatus.RUNNING: {
        SessionStatus.WAITING,
        SessionStatus.COMPLETED,
        SessionStatus.FAILED,
        SessionStatus.CLOSED,
        SessionStatus.LOST,
    },
    SessionStatus.WAITING: {
        SessionStatus.RUNNING,
        SessionStatus.COMPLETED,
        SessionStatus.FAILED,
        SessionStatus.CLOSED,
        SessionStatus.LOST,
    },
    SessionStatus.COMPLETED: {
        SessionStatus.CLOSED,
    },
    SessionStatus.FAILED: {
        SessionStatus.CLOSED,
    },
    SessionStatus.LOST: {
        SessionStatus.RUNNING,
        SessionStatus.CLOSED,
    },
    SessionStatus.CLOSED: set(),  # Terminal state
}


@dataclass
class Session:
    """Represents a persistent terminal session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    status: SessionStatus = SessionStatus.CREATED
    device_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("Session ID cannot be empty.")
        if not isinstance(self.status, SessionStatus):
            try:
                self.status = SessionStatus(self.status)
            except ValueError as err:
                raise ValidationError(f"Invalid session status: {self.status}") from err

    def is_active(self) -> bool:
        """Indicates whether the session is in an active/alive operational state."""
        return self.status in {SessionStatus.CREATED, SessionStatus.RUNNING, SessionStatus.WAITING}

    def is_terminal(self) -> bool:
        """Indicates whether the session has reached a closed terminal state."""
        return self.status == SessionStatus.CLOSED

    def transition_to(self, new_status: SessionStatus) -> None:
        """Transitions session to a new status if the transition is valid."""
        if not isinstance(new_status, SessionStatus):
            try:
                new_status = SessionStatus(new_status)
            except ValueError as err:
                raise ValidationError(f"Invalid target session status: {new_status}") from err

        if new_status == self.status:
            return

        allowed = SESSION_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                current_state=self.status.value,
                target_state=new_status.value,
                entity_type="Session",
            )

        now = datetime.now(timezone.utc)
        self.status = new_status
        self.updated_at = now
        if new_status == SessionStatus.CLOSED:
            self.closed_at = now
