"""Tests for persistence lifecycle: service restart, voluminous output, and secret masking."""

from pathlib import Path
import sys
import time

import pytest

from terminal_session_manager.models.event import Event, EventType
from terminal_session_manager.models.session import Session, SessionStatus
from terminal_session_manager.persistence.sqlite import (
    SqliteEventRepository,
    SqliteSessionRepository,
    SqliteStorage,
)
from terminal_session_manager.services.local_session import LocalSession
from terminal_session_manager.transports.local_process import LocalProcessTransport


def test_service_restart_recovers_session_and_events(tmp_path: Path) -> None:
    db_file = tmp_path / "lifecycle.db"

    # Step 1: Initial service instance
    storage1 = SqliteStorage(db_file)
    session_repo1 = SqliteSessionRepository(storage1)
    event_repo1 = SqliteEventRepository(storage1)

    session = Session(name="persistent-session-1")
    transport1 = LocalProcessTransport(
        command=[
            sys.executable,
            "-u",
            "-c",
            "import sys; line = sys.stdin.readline(); sys.stdout.write(f'ACK: {line}'); sys.stdout.flush()",
        ]
    )
    local_session = LocalSession(
        session=session,
        transport=transport1,
        session_repo=session_repo1,
        event_repo=event_repo1,
    )

    local_session.start()
    local_session.write("hello persistence\n")

    # Read output
    output = ""
    for _ in range(10):
        chunk = local_session.read_text(timeout=0.5)
        output += chunk
        if "ACK: hello persistence" in output:
            break

    assert "ACK: hello persistence" in output

    time.sleep(0.3)
    local_session.close()

    session_id = session.id
    storage1.close()

    # Step 2: Simulate service restart by creating brand new storage and repositories
    storage2 = SqliteStorage(db_file)
    session_repo2 = SqliteSessionRepository(storage2)
    event_repo2 = SqliteEventRepository(storage2)

    recovered_session = session_repo2.get_by_id(session_id)
    assert recovered_session is not None
    assert recovered_session.id == session_id
    assert recovered_session.name == "persistent-session-1"
    assert recovered_session.status == SessionStatus.CLOSED
    assert recovered_session.closed_at is not None

    events = event_repo2.get_events(session_id)
    assert len(events) >= 4

    # Verify event types and sequence
    event_types = [e.event_type for e in events]
    assert EventType.STATE_CHANGE in event_types  # created -> running
    assert EventType.STDIN in event_types         # hello persistence
    assert EventType.STDOUT in event_types        # ACK: hello persistence
    assert EventType.STATE_CHANGE in event_types  # closed

    assert [e.sequence for e in events] == list(range(len(events)))

    storage2.close()


def test_voluminous_output_cursor_pagination(tmp_path: Path) -> None:
    db_file = tmp_path / "large_output.db"
    storage = SqliteStorage(db_file)
    event_repo = SqliteEventRepository(storage)

    total_events = 350
    large_payload = "X" * 2048  # 2KB per event = ~700KB total stream

    for seq in range(total_events):
        event = Event(
            sequence=seq,
            session_id="heavy-session",
            event_type=EventType.STDOUT,
            payload=f"chunk-{seq}:{large_payload}",
        )
        event_repo.append(event)

    # Validate pagination through cursors
    page_size = 50
    retrieved_count = 0
    current_cursor = 0

    while True:
        page = event_repo.get_events(
            session_id="heavy-session",
            since_sequence=current_cursor,
            limit=page_size,
        )
        if not page:
            break

        assert len(page) <= page_size
        for idx, event in enumerate(page):
            expected_seq = current_cursor + idx
            assert event.sequence == expected_seq
            assert event.payload.startswith(f"chunk-{expected_seq}:")

        retrieved_count += len(page)
        current_cursor = page[-1].sequence + 1

    assert retrieved_count == total_events
    storage.close()


def test_sensitive_data_masking_in_history(tmp_path: Path) -> None:
    db_file = tmp_path / "security.db"
    storage = SqliteStorage(db_file)
    session_repo = SqliteSessionRepository(storage)
    event_repo = SqliteEventRepository(storage)

    session = Session(name="secure-session")
    script = (
        "import sys\n"
        "while True:\n"
        "    line = sys.stdin.readline()\n"
        "    if not line or 'exit' in line:\n"
        "        break\n"
    )
    transport = LocalProcessTransport(command=[sys.executable, "-u", "-c", script])
    local_session = LocalSession(
        session=session,
        transport=transport,
        session_repo=session_repo,
        event_repo=event_repo,
    )

    local_session.start()
    raw_secret = "SUPER_SECRET_TOKEN_98765"
    local_session.write(f"{raw_secret}\n", is_sensitive=True)

    local_session.write("exit\n", is_sensitive=False)
    time.sleep(0.3)
    local_session.close()

    events = event_repo.get_events(session.id)
    stdin_events = [e for e in events if e.event_type == EventType.STDIN]
    assert len(stdin_events) == 2

    # Sensitive event
    sensitive_event = stdin_events[0]
    assert sensitive_event.is_masked is True
    assert sensitive_event.payload == "[REDACTED]"
    assert raw_secret not in sensitive_event.payload

    # Raw database check to confirm secret was NEVER written to SQLite
    cursor = storage.connection.execute("SELECT payload FROM events WHERE is_masked = 1;")
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "[REDACTED]"

    # Full text search in the database file confirms raw secret doesn't exist
    cursor = storage.connection.execute(
        "SELECT COUNT(*) FROM events WHERE payload LIKE ?;", (f"%{raw_secret}%",)
    )
    assert cursor.fetchone()[0] == 0

    storage.close()
