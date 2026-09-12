"""Unit tests for SSHTransport using mocked Paramiko client and channel."""

from __future__ import annotations

import io
from pathlib import Path
import socket
import threading
import time
from unittest.mock import MagicMock, patch

import paramiko
import pytest

from terminal_session_manager.errors import (
    TransportClosedError,
    TransportError,
    TransportNotOpenError,
    TransportTimeoutError,
)
from terminal_session_manager.interfaces.transport import TerminalTransport
from terminal_session_manager.transports.ssh import SSHTransport, _load_private_key


class MockChannel:
    """Simulates a Paramiko Channel with in-memory streams and exit status."""

    def __init__(self) -> None:
        self.closed = False
        self._stdout_data = bytearray()
        self._stderr_data = bytearray()
        self._written_data = bytearray()
        self._exit_status: int | None = None
        self._lock = threading.Lock()
        self.rows = 24
        self.cols = 80

    def feed_stdout(self, data: bytes) -> None:
        with self._lock:
            self._stdout_data.extend(data)

    def feed_stderr(self, data: bytes) -> None:
        with self._lock:
            self._stderr_data.extend(data)

    def set_exit_status(self, code: int) -> None:
        with self._lock:
            self._exit_status = code

    def recv_ready(self) -> bool:
        with self._lock:
            return len(self._stdout_data) > 0

    def recv_stderr_ready(self) -> bool:
        with self._lock:
            return len(self._stderr_data) > 0

    def recv(self, max_bytes: int) -> bytes:
        with self._lock:
            if not self._stdout_data:
                return b""
            chunk = bytes(self._stdout_data[:max_bytes])
            del self._stdout_data[:max_bytes]
            return chunk

    def recv_stderr(self, max_bytes: int) -> bytes:
        with self._lock:
            if not self._stderr_data:
                return b""
            chunk = bytes(self._stderr_data[:max_bytes])
            del self._stderr_data[:max_bytes]
            return chunk

    def send(self, data: bytes) -> int:
        if self.closed:
            raise socket.error("Socket is closed")
        with self._lock:
            self._written_data.extend(data)
            return len(data)

    def exec_command(self, cmd: str) -> None:
        self.executed_command = cmd

    def resize_pty(self, width: int = 80, height: int = 24) -> None:
        self.cols = width
        self.rows = height

    def exit_status_ready(self) -> bool:
        with self._lock:
            return self._exit_status is not None

    def recv_exit_status(self) -> int:
        with self._lock:
            return self._exit_status if self._exit_status is not None else 0

    def close(self) -> None:
        self.closed = True


class MockSSHClient:
    """Mock Paramiko SSHClient."""

    def __init__(self) -> None:
        self.connected = False
        self.connect_kwargs: dict = {}
        self.mock_channel = MockChannel()
        self.host_key_policy = None
        self.loaded_host_keys = None
        self.system_host_keys_loaded = False
        self.closed = False

    def load_system_host_keys(self) -> None:
        self.system_host_keys_loaded = True

    def load_host_keys(self, filename: str) -> None:
        self.loaded_host_keys = filename

    def set_missing_host_key_policy(self, policy: Any) -> None:
        self.host_key_policy = policy

    def connect(self, **kwargs) -> None:
        self.connect_kwargs = kwargs
        self.connected = True

    def invoke_shell(self, term: str = "vt100", width: int = 80, height: int = 24) -> MockChannel:
        self.mock_channel.cols = width
        self.mock_channel.rows = height
        return self.mock_channel

    def get_transport(self) -> Any:
        mock_transport = MagicMock()
        mock_transport.open_session.return_value = self.mock_channel
        return mock_transport

    def close(self) -> None:
        self.closed = True
        self.mock_channel.close()


def test_ssh_transport_conforms_to_terminal_transport_protocol():
    """Validates that SSHTransport implements the TerminalTransport protocol."""
    transport = SSHTransport(host="192.168.1.10")
    assert isinstance(transport, TerminalTransport)


def test_ssh_transport_password_auth_lifecycle():
    """Verifies complete interactive shell lifecycle using password authentication."""
    mock_client = MockSSHClient()
    transport = SSHTransport(
        host="192.168.1.10",
        port=2222,
        username="admin",
        password="supersecretpassword",
        client_factory=lambda: mock_client,
    )

    assert not transport.is_alive()
    transport.open()
    assert transport.is_alive()
    assert mock_client.connected
    assert mock_client.connect_kwargs["hostname"] == "192.168.1.10"
    assert mock_client.connect_kwargs["port"] == 2222
    assert mock_client.connect_kwargs["username"] == "admin"
    assert mock_client.connect_kwargs["password"] == "supersecretpassword"

    # Terminal resize
    transport.resize(40, 120)
    assert mock_client.mock_channel.rows == 40
    assert mock_client.mock_channel.cols == 120

    # Write and read
    mock_client.mock_channel.feed_stdout(b"Welcome to remote host\r\n$ ")
    data = transport.read(max_bytes=1024, timeout=0.5)
    assert b"Welcome to remote host" in data

    written = transport.write(b"uname -a\n")
    assert written == len(b"uname -a\n")
    assert bytes(mock_client.mock_channel._written_data) == b"uname -a\n"

    # Close
    transport.close()
    assert not transport.is_alive()
    assert mock_client.closed


def test_ssh_transport_private_key_auth(tmp_path):
    """Verifies private key loading and connection kwargs."""
    # Generate temporary RSA key
    key_file = io.StringIO()
    rsa_key = paramiko.RSAKey.generate(1024)
    rsa_key.write_private_key(key_file)
    key_str = key_file.getvalue()

    mock_client = MockSSHClient()
    transport = SSHTransport(
        host="srv.corp.internal",
        username="deployer",
        private_key=key_str,
        client_factory=lambda: mock_client,
    )

    transport.open()
    assert mock_client.connected
    assert mock_client.connect_kwargs["username"] == "deployer"
    assert "pkey" in mock_client.connect_kwargs
    assert isinstance(mock_client.connect_kwargs["pkey"], paramiko.RSAKey)
    transport.close()


def test_ssh_transport_strict_host_key_checking_rejects_by_default(tmp_path):
    """Verifies that strict_host_key_checking uses RejectPolicy and never AutoAddPolicy."""
    mock_client = MockSSHClient()
    known_hosts_file = tmp_path / "known_hosts"
    known_hosts_file.write_text("# empty known_hosts\n", encoding="utf-8")

    transport = SSHTransport(
        host="unknown-server.internal",
        known_hosts_path=str(known_hosts_file),
        strict_host_key_checking=True,
        client_factory=lambda: mock_client,
    )

    transport.open()
    assert isinstance(mock_client.host_key_policy, paramiko.RejectPolicy)
    assert mock_client.loaded_host_keys == str(known_hosts_file)
    transport.close()


def test_ssh_transport_auth_failure_error_handling_masks_secrets():
    """Verifies that authentication errors raise TransportError without leaking password."""
    def failing_client_factory():
        client = MockSSHClient()
        def fail_connect(**kwargs):
            raise paramiko.AuthenticationException("Authentication failed.")
        client.connect = fail_connect
        return client

    secret_pw = "super_classified_secret_123"
    transport = SSHTransport(
        host="bastion.internal",
        username="ops",
        password=secret_pw,
        client_factory=failing_client_factory,
    )

    with pytest.raises(TransportError) as exc_info:
        transport.open()

    err_msg = str(exc_info.value)
    assert "SSH authentication failed" in err_msg
    assert "ops" in err_msg
    assert secret_pw not in err_msg  # Invariant: password never exposed in error message


def test_ssh_transport_host_key_verification_failure():
    """Verifies that host key mismatch or missing host key raises TransportError."""
    def host_key_failing_client():
        client = MockSSHClient()
        def fail_connect(**kwargs):
            raise paramiko.SSHException("Server 'bad.host' not found in known_hosts")
        client.connect = fail_connect
        return client

    transport = SSHTransport(
        host="bad.host",
        client_factory=host_key_failing_client,
    )

    with pytest.raises(TransportError) as exc_info:
        transport.open()

    assert "Host key verification failed" in str(exc_info.value)


def test_ssh_transport_timeout_handling():
    """Verifies that connection timeouts raise TransportTimeoutError."""
    def timeout_client():
        client = MockSSHClient()
        def fail_connect(**kwargs):
            raise socket.timeout("timed out")
        client.connect = fail_connect
        return client

    transport = SSHTransport(
        host="slow.host.internal",
        connect_timeout=0.1,
        client_factory=timeout_client,
    )

    with pytest.raises(TransportTimeoutError) as exc_info:
        transport.open()

    assert "Connection timed out" in str(exc_info.value)


def test_ssh_transport_command_exec_and_exit_code():
    """Verifies command execution mode capturing exit code and stderr."""
    mock_client = MockSSHClient()
    transport = SSHTransport(
        host="compute-node-1",
        command="echo hello && exit 42",
        client_factory=lambda: mock_client,
    )

    transport.open()
    mock_client.mock_channel.feed_stdout(b"hello\n")
    mock_client.mock_channel.feed_stderr(b"warning: test stderr\n")
    mock_client.mock_channel.set_exit_status(42)

    time.sleep(0.05)
    stdout = transport.read(max_bytes=1024, timeout=0.2)
    stderr = transport.read_stderr(max_bytes=1024, timeout=0.2)

    assert b"hello" in stdout
    assert b"warning: test stderr" in stderr
    assert transport.exit_code == 42

    transport.close()


def test_ssh_transport_write_when_not_open_raises_error():
    """Verifies write and read reject operations when transport is not open."""
    transport = SSHTransport(host="test-srv")
    with pytest.raises(TransportNotOpenError):
        transport.write(b"data")
    with pytest.raises(TransportNotOpenError):
        transport.read(1024)
