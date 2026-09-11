"""Tests for LocalSession controller and lifecycle integration."""

import sys
import time

import pytest

from terminal_session_manager.errors import TransportClosedError, TransportError
from terminal_session_manager.models.session import Session, SessionStatus
from terminal_session_manager.services.local_session import LocalSession
from terminal_session_manager.transports.local_process import LocalProcessTransport


def test_session_successful_lifecycle() -> None:
    session_entity = Session(name="oneshot-success")
    transport = LocalProcessTransport(
        command=[
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('DONE'); sys.stdout.flush()",
        ]
    )
    local_session = LocalSession(session=session_entity, transport=transport)

    assert local_session.status == SessionStatus.CREATED

    local_session.start()
    assert local_session.session.status == SessionStatus.RUNNING

    output = local_session.read_text(timeout=1.0)
    assert "DONE" in output

    # Wait for process to exit
    time.sleep(0.3)
    assert local_session.poll_status() == SessionStatus.COMPLETED
    assert local_session.session.metadata.get("exit_code") == 0

    local_session.close()
    assert local_session.session.status == SessionStatus.CLOSED


def test_session_failure_on_non_zero_exit() -> None:
    session_entity = Session(name="failing-command")
    transport = LocalProcessTransport(
        command=[sys.executable, "-c", "import sys; sys.exit(7)"]
    )
    local_session = LocalSession(session=session_entity, transport=transport)

    local_session.start()
    assert local_session.session.status == SessionStatus.RUNNING

    # Read triggers status poll
    _ = local_session.read(timeout=0.5)
    time.sleep(0.3)

    assert local_session.poll_status() == SessionStatus.FAILED
    assert local_session.session.metadata.get("exit_code") == 7

    local_session.close()
    assert local_session.session.status == SessionStatus.CLOSED


def test_session_start_failure_transitions_to_failed() -> None:
    session_entity = Session(name="bad-binary")
    transport = LocalProcessTransport(command=["invalid_command_binary_xyz"])
    local_session = LocalSession(session=session_entity, transport=transport)

    with pytest.raises(TransportError):
        local_session.start()

    assert local_session.session.status == SessionStatus.FAILED
    assert "start_error" in local_session.session.metadata


def test_interactive_session_write_and_read() -> None:
    script = (
        "import sys\n"
        "while True:\n"
        "    line = sys.stdin.readline()\n"
        "    if not line or line.strip() == 'quit':\n"
        "        break\n"
        "    sys.stdout.write(f'PROCESSED: {line}')\n"
        "    sys.stdout.flush()\n"
    )
    transport = LocalProcessTransport(command=[sys.executable, "-u", "-c", script])
    local_session = LocalSession(transport=transport)

    local_session.start()
    try:
        assert local_session.status == SessionStatus.RUNNING

        local_session.write("hello session\n")
        response = ""
        for _ in range(10):
            chunk = local_session.read_text(timeout=0.5)
            response += chunk
            if "PROCESSED: hello session" in response:
                break

        assert "PROCESSED: hello session" in response

        # Send quit to finish process
        local_session.write("quit\n")
        time.sleep(0.3)
        assert local_session.poll_status() == SessionStatus.COMPLETED
    finally:
        local_session.close()

    assert local_session.session.status == SessionStatus.CLOSED


def test_write_to_closed_session_raises() -> None:
    local_session = LocalSession()
    with pytest.raises(TransportClosedError, match="session is not running"):
        local_session.write("should fail")


class FakeTransport:
    """Mock transport verifying pluggability and independence from OS processes."""

    def __init__(self) -> None:
        self.opened = False
        self.closed = False
        self.alive = False
        self.buffer = b""

    def open(self) -> None:
        self.opened = True
        self.alive = True

    def read(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        data = self.buffer[:max_bytes]
        self.buffer = self.buffer[max_bytes:]
        return data

    def write(self, data: bytes) -> int:
        self.buffer += data
        return len(data)

    def resize(self, rows: int, cols: int) -> None:
        pass

    def close(self) -> None:
        self.closed = True
        self.alive = False

    def is_alive(self) -> bool:
        return self.alive


def test_pluggable_transport_with_local_session() -> None:
    fake_transport = FakeTransport()
    session = LocalSession(transport=fake_transport)

    session.start()
    assert fake_transport.opened is True
    assert session.status == SessionStatus.RUNNING

    session.write("custom transport data")
    assert session.read_text() == "custom transport data"

    session.close()
    assert fake_transport.closed is True
    assert session.session.status == SessionStatus.CLOSED
