"""Unit tests for Event model, ordering, and session/job correlation."""

from datetime import datetime, timezone

import pytest

from terminal_session_manager.errors import ValidationError
from terminal_session_manager.models.event import Event, EventType


def test_event_creation_and_defaults() -> None:
    event = Event(
        sequence=0,
        session_id="session-42",
        event_type=EventType.STDOUT,
        payload="Welcome to shell",
    )
    assert event.id is not None
    assert event.sequence == 0
    assert event.session_id == "session-42"
    assert event.job_id is None
    assert event.event_type == EventType.STDOUT
    assert event.payload == "Welcome to shell"
    assert event.is_masked is False
    assert event.timestamp is not None


def test_event_linked_to_job() -> None:
    event = Event(
        sequence=1,
        session_id="session-42",
        job_id="job-99",
        event_type=EventType.STDIN,
        payload="echo secure_token",
        is_masked=True,
    )
    assert event.session_id == "session-42"
    assert event.job_id == "job-99"
    assert event.is_masked is True
    assert event.event_type == EventType.STDIN


def test_event_validation_errors() -> None:
    with pytest.raises(ValidationError, match="session_id"):
        Event(sequence=0, session_id="", event_type=EventType.STDOUT, payload="test")

    with pytest.raises(ValidationError, match="non-negative"):
        Event(sequence=-1, session_id="s1", event_type=EventType.STDOUT, payload="test")

    with pytest.raises(ValidationError, match="Invalid event type"):
        Event(
            sequence=0,
            session_id="s1",
            event_type="unknown_type",  # type: ignore[arg-type]
            payload="test",
        )


def test_event_strict_ordering_by_sequence() -> None:
    e0 = Event(sequence=0, session_id="s1", event_type=EventType.SYSTEM, payload="init")
    e1 = Event(sequence=1, session_id="s1", event_type=EventType.STDOUT, payload="out1")
    e2 = Event(sequence=2, session_id="s1", event_type=EventType.STDERR, payload="err")
    e3 = Event(sequence=3, session_id="s1", event_type=EventType.STATE_CHANGE, payload="closed")

    unsorted_events = [e2, e0, e3, e1]
    sorted_events = sorted(unsorted_events)

    assert sorted_events == [e0, e1, e2, e3]
    assert sorted_events[0].sequence == 0
    assert sorted_events[1].sequence == 1
    assert sorted_events[2].sequence == 2
    assert sorted_events[3].sequence == 3


def test_event_ordering_with_same_sequence_resolves_by_timestamp() -> None:
    t1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 12, 0, 1, tzinfo=timezone.utc)

    e_early = Event(
        sequence=10,
        session_id="s1",
        event_type=EventType.STDOUT,
        payload="first",
        timestamp=t1,
    )
    e_later = Event(
        sequence=10,
        session_id="s1",
        event_type=EventType.STDOUT,
        payload="second",
        timestamp=t2,
    )

    assert e_early < e_later
    assert sorted([e_later, e_early]) == [e_early, e_later]
