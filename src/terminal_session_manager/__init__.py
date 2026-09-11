"""Terminal Session Manager — Minimalist persistent terminal architecture for agents."""

__version__ = "0.1.0"

from terminal_session_manager.errors import (
    CredentialNotFoundError,
    DeviceNotFoundError,
    DomainError,
    EntityNotFoundError,
    InvalidStateError,
    InvalidStateTransitionError,
    JobNotFoundError,
    SessionNotFoundError,
    TransportClosedError,
    TransportError,
    TransportNotOpenError,
    TransportTimeoutError,
    ValidationError,
)
from terminal_session_manager.models import (
    ConnectionMethod,
    CredentialRef,
    CredentialType,
    Device,
    DeviceType,
    Event,
    EventType,
    Job,
    JobStatus,
    Session,
    SessionStatus,
)
from terminal_session_manager.persistence import (
    SqliteEventRepository,
    SqliteJobRepository,
    SqliteSessionRepository,
    SqliteStorage,
)
from terminal_session_manager.services import LocalSession
from terminal_session_manager.transports import LocalProcessTransport

__all__ = [
    "__version__",
    "ConnectionMethod",
    "CredentialNotFoundError",
    "CredentialRef",
    "CredentialType",
    "Device",
    "DeviceNotFoundError",
    "DeviceType",
    "DomainError",
    "EntityNotFoundError",
    "Event",
    "EventType",
    "InvalidStateError",
    "InvalidStateTransitionError",
    "Job",
    "JobNotFoundError",
    "JobStatus",
    "LocalProcessTransport",
    "LocalSession",
    "Session",
    "SessionNotFoundError",
    "SessionStatus",
    "SqliteEventRepository",
    "SqliteJobRepository",
    "SqliteSessionRepository",
    "SqliteStorage",
    "TransportClosedError",
    "TransportError",
    "TransportNotOpenError",
    "TransportTimeoutError",
    "ValidationError",
]
