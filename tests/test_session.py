"""Unit tests for Session model and lifecycle transitions."""

import pytest

from terminal_session_manager.errors import InvalidStateTransitionError, ValidationError
from terminal_session_manager.models.session import Session, SessionStatus


def test_session_creation_defaults() -> None:
    session = Session(name="local-worker")
    assert session.id is not None
    assert session.name == "local-worker"
    assert session.status == SessionStatus.CREATED
    assert session.is_active() is True
    assert session.is_terminal() is False
    assert session.created_at is not None
    assert session.updated_at is not None
    assert session.closed_at is None
    assert session.metadata == {}


def test_session_invalid_status() -> None:
    with pytest.raises(ValidationError):
        Session(status="non_existent_status")  # type: ignore[arg-type]


def test_session_empty_id_raises() -> None:
    with pytest.raises(ValidationError, match="cannot be empty"):
        Session(id="")


def test_valid_transitions() -> None:
    session = Session(name="interactive-test")

    # CREATED -> RUNNING
    session.transition_to(SessionStatus.RUNNING)
    assert session.status == SessionStatus.RUNNING
    assert session.is_active() is True

    # RUNNING -> WAITING
    session.transition_to(SessionStatus.WAITING)
    assert session.status == SessionStatus.WAITING

    # WAITING -> RUNNING
    session.transition_to(SessionStatus.RUNNING)
    assert session.status == SessionStatus.RUNNING

    # RUNNING -> LOST
    session.transition_to(SessionStatus.LOST)
    assert session.status == SessionStatus.LOST
    assert session.is_active() is False

    # LOST -> RUNNING (reconnection)
    session.transition_to(SessionStatus.RUNNING)
    assert session.status == SessionStatus.RUNNING

    # RUNNING -> COMPLETED
    session.transition_to(SessionStatus.COMPLETED)
    assert session.status == SessionStatus.COMPLETED

    # COMPLETED -> CLOSED
    session.transition_to(SessionStatus.CLOSED)
    assert session.status == SessionStatus.CLOSED
    assert session.is_terminal() is True
    assert session.closed_at is not None


def test_transition_idempotent_when_same_state() -> None:
    session = Session()
    session.transition_to(SessionStatus.CREATED)
    assert session.status == SessionStatus.CREATED


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (SessionStatus.CLOSED, SessionStatus.RUNNING),
        (SessionStatus.CLOSED, SessionStatus.CREATED),
        (SessionStatus.COMPLETED, SessionStatus.RUNNING),
        (SessionStatus.FAILED, SessionStatus.RUNNING),
        (SessionStatus.CREATED, SessionStatus.WAITING),
        (SessionStatus.CREATED, SessionStatus.COMPLETED),
        (SessionStatus.CREATED, SessionStatus.LOST),
    ],
)
def test_invalid_transitions_rejected(
    from_status: SessionStatus, to_status: SessionStatus
) -> None:
    session = Session(status=from_status)
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        session.transition_to(to_status)

    assert exc_info.value.current_state == from_status.value
    assert exc_info.value.target_state == to_status.value
    assert exc_info.value.entity_type == "Session"
