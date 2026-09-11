"""Persistence interfaces for sessions, jobs, and events."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from terminal_session_manager.models.event import Event
from terminal_session_manager.models.job import Job
from terminal_session_manager.models.session import Session


@runtime_checkable
class SessionRepository(Protocol):
    """Contract for session persistence."""

    def save(self, session: Session) -> None:
        """Persists or updates a session."""
        ...

    def get_by_id(self, session_id: str) -> Session | None:
        """Retrieves a session by ID or returns None if not found."""
        ...

    def list_all(self) -> list[Session]:
        """Lists all persisted sessions."""
        ...


@runtime_checkable
class JobRepository(Protocol):
    """Contract for job persistence."""

    def save(self, job: Job) -> None:
        """Persists or updates a job."""
        ...

    def get_by_id(self, job_id: str) -> Job | None:
        """Retrieves a job by ID or returns None if not found."""
        ...

    def list_by_session(self, session_id: str) -> list[Job]:
        """Lists all jobs associated with a given session ID."""
        ...


@runtime_checkable
class EventRepository(Protocol):
    """Contract for event stream persistence and cursor-based retrieval."""

    def append(self, event: Event) -> None:
        """Appends a new event to the session/job stream."""
        ...

    def get_events(
        self,
        session_id: str,
        since_sequence: int = 0,
        limit: int | None = None,
    ) -> list[Event]:
        """Retrieves an ordered stream of events for a session from a sequence cursor."""
        ...
