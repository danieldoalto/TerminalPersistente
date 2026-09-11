"""Unit tests for SQLite persistence repositories and constraints."""

from datetime import datetime, timezone
import pytest

from terminal_session_manager.errors import ValidationError
from terminal_session_manager.interfaces.persistence import (
    EventRepository,
    JobRepository,
    SessionRepository,
)
from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.job import Job, JobStatus
from terminal_session_manager.models.session import Session, SessionStatus
from terminal_session_manager.persistence.sqlite import (
    SqliteEventRepository,
    SqliteJobRepository,
    SqliteSessionRepository,
    SqliteStorage,
)


@pytest.fixture
def storage() -> SqliteStorage:
    """Fixture providing an in-memory SQLite storage."""
    s = SqliteStorage(":memory:")
    yield s
    s.close()


def test_repositories_conform_to_protocols(storage: SqliteStorage) -> None:
    session_repo = SqliteSessionRepository(storage)
    job_repo = SqliteJobRepository(storage)
    event_repo = SqliteEventRepository(storage)

    assert isinstance(session_repo, SessionRepository)
    assert isinstance(job_repo, JobRepository)
    assert isinstance(event_repo, EventRepository)


def test_sqlite_session_repository_crud(storage: SqliteStorage) -> None:
    repo = SqliteSessionRepository(storage)

    # Absence check
    assert repo.get_by_id("non_existent") is None

    session = Session(name="sess-primary", metadata={"env": "test"})
    repo.save(session)

    retrieved = repo.get_by_id(session.id)
    assert retrieved is not None
    assert retrieved.id == session.id
    assert retrieved.name == "sess-primary"
    assert retrieved.status == SessionStatus.CREATED
    assert retrieved.metadata == {"env": "test"}

    # Update (Upsert)
    session.transition_to(SessionStatus.RUNNING)
    session.metadata["updated"] = True
    repo.save(session)

    updated = repo.get_by_id(session.id)
    assert updated is not None
    assert updated.status == SessionStatus.RUNNING
    assert updated.metadata["updated"] is True

    # List
    session2 = Session(name="sess-secondary")
    repo.save(session2)
    sessions = repo.list_all()
    assert len(sessions) == 2


def test_sqlite_job_repository_crud(storage: SqliteStorage) -> None:
    repo = SqliteJobRepository(storage)

    assert repo.get_by_id("job_404") is None

    job1 = Job(session_id="sess-1", command="echo 1")
    job2 = Job(session_id="sess-1", command="echo 2")
    job3 = Job(session_id="sess-2", command="echo 3")

    repo.save(job1)
    repo.save(job2)
    repo.save(job3)

    assert repo.get_by_id(job1.id) is not None
    assert len(repo.list_by_session("sess-1")) == 2
    assert len(repo.list_by_session("sess-2")) == 1

    # Update job status and outputs
    job1.transition_to(JobStatus.RUNNING)
    job1.stdout = "output-1"
    job1.transition_to(JobStatus.COMPLETED, exit_code=0)
    repo.save(job1)

    updated_job = repo.get_by_id(job1.id)
    assert updated_job is not None
    assert updated_job.status == JobStatus.COMPLETED
    assert updated_job.exit_code == 0
    assert updated_job.stdout == "output-1"


def test_sqlite_event_repository_ordering_and_cursor(storage: SqliteStorage) -> None:
    repo = SqliteEventRepository(storage)

    # Empty history
    assert repo.get_events("sess-1") == []
    assert repo.get_latest_sequence("sess-1") == -1

    # Insert events
    for seq in range(5):
        event = Event(
            sequence=seq,
            session_id="sess-1",
            event_type=EventType.STDOUT,
            payload=f"chunk-{seq}",
        )
        repo.append(event)

    assert repo.get_latest_sequence("sess-1") == 4

    # Full retrieval
    all_events = repo.get_events("sess-1")
    assert len(all_events) == 5
    assert [e.sequence for e in all_events] == [0, 1, 2, 3, 4]

    # Incremental retrieval by cursor (since_sequence)
    cursor_events = repo.get_events("sess-1", since_sequence=2)
    assert len(cursor_events) == 3
    assert [e.sequence for e in cursor_events] == [2, 3, 4]

    # Limit
    limited = repo.get_events("sess-1", since_sequence=1, limit=2)
    assert len(limited) == 2
    assert [e.sequence for e in limited] == [1, 2]


def test_sqlite_event_repository_rejects_duplicate_sequence(storage: SqliteStorage) -> None:
    repo = SqliteEventRepository(storage)

    e1 = Event(sequence=0, session_id="sess-1", event_type=EventType.SYSTEM, payload="start")
    repo.append(e1)

    # Attempt duplicate sequence 0 for same session
    e2 = Event(sequence=0, session_id="sess-1", event_type=EventType.STDOUT, payload="dup")
    with pytest.raises(ValidationError, match="Duplicate sequence"):
        repo.append(e2)

    # Different session can have sequence 0
    e3 = Event(sequence=0, session_id="sess-2", event_type=EventType.SYSTEM, payload="start")
    repo.append(e3)
    assert len(repo.get_events("sess-2")) == 1
