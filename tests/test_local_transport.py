"""Tests for LocalProcessTransport adapter."""

import sys
import time

import pytest

from terminal_session_manager.errors import (
    TransportClosedError,
    TransportError,
    TransportNotOpenError,
)
from terminal_session_manager.interfaces.transport import TerminalTransport
from terminal_session_manager.transports.local_process import LocalProcessTransport


def test_conforms_to_terminal_transport_protocol() -> None:
    transport = LocalProcessTransport()
    assert isinstance(transport, TerminalTransport)


def test_unopened_transport_raises() -> None:
    transport = LocalProcessTransport()
    with pytest.raises(TransportNotOpenError):
        transport.read()

    with pytest.raises(TransportNotOpenError):
        transport.write(b"test")


def test_command_not_found_raises_transport_error() -> None:
    transport = LocalProcessTransport(command=["non_existent_executable_12345"])
    with pytest.raises(TransportError, match="Command not found"):
        transport.open()


def test_oneshot_command_execution() -> None:
    transport = LocalProcessTransport(
        command=[
            sys.executable,
            "-c",
            "import sys; print('TSM_TEST_OUTPUT'); sys.stdout.flush()",
        ]
    )
    transport.open()
    assert transport.is_alive() is True

    # Read output
    output = b""
    for _ in range(10):
        chunk = transport.read(timeout=0.5)
        if chunk:
            output += chunk
        if b"TSM_TEST_OUTPUT" in output:
            break

    assert b"TSM_TEST_OUTPUT" in output

    # Wait for natural exit
    time.sleep(0.2)
    assert transport.is_alive() is False
    assert transport.exit_code == 0
    transport.close()


def test_interactive_io() -> None:
    # Echo back whatever is sent via stdin
    script = (
        "import sys\n"
        "for line in sys.stdin:\n"
        "    sys.stdout.write(f'ECHO: {line}')\n"
        "    sys.stdout.flush()\n"
    )
    transport = LocalProcessTransport(command=[sys.executable, "-u", "-c", script])
    transport.open()
    try:
        assert transport.is_alive() is True

        transport.write(b"hello world\n")

        # Read back response
        response = b""
        for _ in range(10):
            chunk = transport.read(timeout=0.5)
            if chunk:
                response += chunk
            if b"ECHO: hello world" in response:
                break

        assert b"ECHO: hello world" in response
    finally:
        transport.close()

    assert transport.is_alive() is False


def test_read_timeout_non_blocking() -> None:
    # A script that sleeps without producing output
    transport = LocalProcessTransport(
        command=[sys.executable, "-c", "import time; time.sleep(5)"]
    )
    transport.open()
    try:
        start = time.monotonic()
        data = transport.read(timeout=0.1)
        elapsed = time.monotonic() - start

        assert data == b""
        assert elapsed < 1.0
    finally:
        transport.close()


def test_write_to_terminated_process_raises_closed_error() -> None:
    transport = LocalProcessTransport(
        command=[sys.executable, "-c", "import sys; sys.exit(0)"]
    )
    transport.open()

    # Wait for process to exit
    time.sleep(0.3)
    assert transport.is_alive() is False

    with pytest.raises(TransportClosedError):
        transport.write(b"too late")

    transport.close()


def test_resize_records_dimensions() -> None:
    transport = LocalProcessTransport()
    transport.resize(rows=40, cols=120)
    assert transport._rows == 40
    assert transport._cols == 120

    with pytest.raises(ValueError):
        transport.resize(rows=0, cols=80)
