"""Domain interfaces and contracts package."""

from terminal_session_manager.interfaces.credentials import CredentialResolver
from terminal_session_manager.interfaces.device import DeviceRepository
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    JobRepository,
    SessionRepository,
)
from terminal_session_manager.interfaces.transport import TerminalTransport

__all__ = [
    "CredentialResolver",
    "DeviceRepository",
    "EventRepository",
    "JobRepository",
    "SessionRepository",
    "TerminalTransport",
]
