"""Event domain model with ordering and session/job linkage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import total_ordering
from typing import Any
import uuid

from terminal_session_manager.errors import ValidationError


class EventType(str, Enum):
    """Categorization of terminal and lifecycle events."""

    STDIN = "stdin"
    STDOUT = "stdout"
    STDERR = "stderr"
    STATE_CHANGE = "state_change"
    SYSTEM = "system"


@total_ordering
@dataclass
class Event:
    """Represents an observable, ordered event within a session or job stream."""

    sequence: int
    session_id: str
    event_type: EventType
    payload: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_masked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("Event ID cannot be empty.")
        if not self.session_id:
            raise ValidationError("Event must be linked to a valid session_id.")
        if self.sequence < 0:
            raise ValidationError("Event sequence must be a non-negative integer.")

        if not isinstance(self.event_type, EventType):
            try:
                self.event_type = EventType(self.event_type)
            except ValueError as err:
                raise ValidationError(f"Invalid event type: {self.event_type}") from err

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return (self.sequence, self.timestamp, self.id) == (
            other.sequence,
            other.timestamp,
            other.id,
        )

    def __lt__(self, other: object) -> bool:
        """Enables natural sorting of events by sequence number and timestamp."""
        if not isinstance(other, Event):
            return NotImplemented
        return (self.sequence, self.timestamp) < (other.sequence, other.timestamp)
