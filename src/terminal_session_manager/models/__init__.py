"""Domain models package for Terminal Session Manager."""

from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.job import JOB_TRANSITIONS, Job, JobStatus
from terminal_session_manager.models.session import (
    SESSION_TRANSITIONS,
    Session,
    SessionStatus,
)

__all__ = [
    "CredentialRef",
    "CredentialType",
    "Device",
    "DeviceType",
    "ConnectionMethod",
    "Event",
    "EventType",
    "Job",
    "JobStatus",
    "JOB_TRANSITIONS",
    "Session",
    "SessionStatus",
    "SESSION_TRANSITIONS",
]
