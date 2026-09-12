"""SSH terminal and command execution transport adapter."""

from __future__ import annotations

import io
import os
from pathlib import Path
import queue
import socket
import threading
import time
from typing import Any, Callable, Sequence

import paramiko

from terminal_session_manager.errors import (
    TransportClosedError,
    TransportError,
    TransportNotOpenError,
    TransportTimeoutError,
)


def _load_private_key(key_data: str | bytes, passphrase: str | None = None) -> paramiko.PKey:
    """Attempts to parse an SSH private key without leaking contents on failure."""
    if isinstance(key_data, bytes):
        key_str = key_data.decode("utf-8", errors="replace")
    else:
        key_str = key_data

    key_file = io.StringIO(key_str.strip())
    loaders = [
        paramiko.RSAKey.from_private_key,
        paramiko.Ed25519Key.from_private_key,
        paramiko.ECDSAKey.from_private_key,
    ]
    if hasattr(paramiko, "DSSKey"):
        loaders.append(getattr(paramiko, "DSSKey").from_private_key)

    for loader in loaders:
        key_file.seek(0)
        try:
            return loader(key_file, password=passphrase)
        except Exception:
            continue

    raise TransportError("Failed to parse private key: invalid or unsupported key format.")


class SSHTransport:
    """TerminalTransport adapter backed by an SSH connection using Paramiko.

    Supports interactive shells (PTY) and command execution, password or
    private key authentication, strict host key verification, and clean timeouts.
    """

    def __init__(
        self,
        host: str,
        port: int = 22,
        username: str | None = None,
        password: str | None = None,
        private_key: str | bytes | None = None,
        passphrase: str | None = None,
        known_hosts_path: str | None = None,
        strict_host_key_checking: bool = True,
        connect_timeout: float = 10.0,
        command: Sequence[str] | str | None = None,
        options: dict[str, Any] | None = None,
        client_factory: Callable[[], paramiko.SSHClient] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self._password = password
        self._private_key = private_key
        self._passphrase = passphrase
        self.known_hosts_path = known_hosts_path
        self.strict_host_key_checking = strict_host_key_checking
        self.connect_timeout = connect_timeout
        self.command = command
        self.options = options or {}
        self._client_factory = client_factory or paramiko.SSHClient

        self._client: paramiko.SSHClient | None = None
        self._channel: paramiko.Channel | None = None
        self._reader_thread: threading.Thread | None = None
        self._output_queue: queue.Queue[bytes | None] = queue.Queue()
        self._stderr_queue: queue.Queue[bytes | None] = queue.Queue()
        self._internal_buffer = bytearray()
        self._internal_stderr_buffer = bytearray()

        self._rows = 24
        self._cols = 80
        self._opened = False
        self._closed = False
        self._stdout_eof = False
        self._stderr_eof = False

    @property
    def exit_code(self) -> int | None:
        """Returns remote exit code or None if channel is still active."""
        if self._channel is None:
            return None
        if self._channel.exit_status_ready():
            return self._channel.recv_exit_status()
        return None

    def open(self) -> None:
        """Establishes the SSH connection and opens the session/shell channel."""
        if self._opened:
            return

        client = self._client_factory()
        self._client = client

        # 1. Host key verification policy
        if self.known_hosts_path and Path(self.known_hosts_path).is_file():
            try:
                client.load_host_keys(self.known_hosts_path)
            except Exception as err:
                raise TransportError(f"Failed to load known_hosts from '{self.known_hosts_path}': {err}") from err
        else:
            try:
                client.load_system_host_keys()
            except Exception:
                pass

        if self.strict_host_key_checking:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 2. Authentication setup
        pkey: paramiko.PKey | None = None
        if self._private_key:
            pkey = _load_private_key(self._private_key, passphrase=self._passphrase)

        connect_kwargs: dict[str, Any] = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "timeout": self.connect_timeout,
            "banner_timeout": self.connect_timeout,
            "auth_timeout": self.connect_timeout,
        }

        if pkey is not None:
            connect_kwargs["pkey"] = pkey
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False
        elif self._password is not None:
            connect_kwargs["password"] = self._password
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False

        # 3. Connect to remote SSH server
        try:
            client.connect(**connect_kwargs)
        except paramiko.AuthenticationException as err:
            raise TransportError(
                f"SSH authentication failed for user '{self.username}' on host '{self.host}:{self.port}'."
            ) from err
        except paramiko.BadHostKeyException as err:
            raise TransportError(
                f"Host key verification failed for host '{self.host}:{self.port}': host key mismatch."
            ) from err
        except (paramiko.SSHException, socket.error) as err:
            err_msg = str(err)
            if "not found in known_hosts" in err_msg or "Host key" in err_msg:
                raise TransportError(
                    f"Host key verification failed for host '{self.host}:{self.port}': unknown host key."
                ) from err
            if isinstance(err, (socket.timeout, TimeoutError)):
                raise TransportTimeoutError(
                    f"Connection timed out connecting to SSH host '{self.host}:{self.port}'."
                ) from err
            raise TransportError(f"SSH connection failed to '{self.host}:{self.port}': {err_msg}") from err

        # 4. Open channel (shell or exec)
        try:
            if self.command is None:
                # Interactive shell session
                self._channel = client.invoke_shell(
                    term="vt100",
                    width=self._cols,
                    height=self._rows,
                )
            else:
                # One-off command execution
                cmd_str = self.command if isinstance(self.command, str) else " ".join(self.command)
                transport = client.get_transport()
                if transport is None:
                    raise TransportError("SSH transport is not available after connection.")
                self._channel = transport.open_session()
                self._channel.exec_command(cmd_str)
        except Exception as err:
            self.close()
            raise TransportError(f"Failed to open SSH channel on '{self.host}:{self.port}': {err}") from err

        self._opened = True
        self._closed = False
        self._eof_reached = False

        # 5. Start asynchronous reader thread
        self._reader_thread = threading.Thread(
            target=self._reader_worker,
            daemon=True,
            name=f"ssh-transport-reader-{self.host}:{self.port}",
        )
        self._reader_thread.start()

    def _reader_worker(self) -> None:
        """Reads stdout and stderr streams from the SSH channel into queues."""
        assert self._channel is not None
        channel = self._channel

        while not self._closed:
            try:
                # Check channel state
                has_data = False
                if channel.recv_ready():
                    chunk = channel.recv(1024)
                    if chunk:
                        self._output_queue.put(chunk)
                        has_data = True

                if channel.recv_stderr_ready():
                    err_chunk = channel.recv_stderr(1024)
                    if err_chunk:
                        self._stderr_queue.put(err_chunk)
                        has_data = True

                if not has_data:
                    if channel.exit_status_ready() or channel.closed:
                        # Flush any remaining bytes before exiting
                        while channel.recv_ready():
                            rem = channel.recv(1024)
                            if rem:
                                self._output_queue.put(rem)
                        while channel.recv_stderr_ready():
                            rem_err = channel.recv_stderr(1024)
                            if rem_err:
                                self._stderr_queue.put(rem_err)
                        break
                    time.sleep(0.02)
            except Exception:
                break

        self._output_queue.put(None)
        self._stderr_queue.put(None)

    def read(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        """Reads up to max_bytes from the SSH stdout stream."""
        if not self._opened:
            raise TransportNotOpenError()
        if max_bytes <= 0:
            return b""

        return self._drain_queue(
            q=self._output_queue,
            buffer=self._internal_buffer,
            max_bytes=max_bytes,
            timeout=timeout,
            eof_attr="_stdout_eof",
        )

    def read_stderr(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        """Reads up to max_bytes from the SSH stderr stream."""
        if not self._opened:
            raise TransportNotOpenError()
        if max_bytes <= 0:
            return b""

        return self._drain_queue(
            q=self._stderr_queue,
            buffer=self._internal_stderr_buffer,
            max_bytes=max_bytes,
            timeout=timeout,
            eof_attr="_stderr_eof",
        )

    def _drain_queue(
        self,
        q: queue.Queue[bytes | None],
        buffer: bytearray,
        max_bytes: int,
        timeout: float | None,
        eof_attr: str,
    ) -> bytes:
        start_time = time.monotonic()
        remaining_timeout = timeout

        while len(buffer) == 0 and not getattr(self, eof_attr):
            try:
                if remaining_timeout is None:
                    item = q.get(timeout=0.2)
                elif remaining_timeout <= 0:
                    item = q.get_nowait()
                else:
                    item = q.get(timeout=remaining_timeout)

                if item is None:
                    setattr(self, eof_attr, True)
                    q.put(None)  # Preserve EOF sentinel
                    break
                buffer.extend(item)
            except queue.Empty:
                if remaining_timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed >= (timeout or 0):
                        break
                    remaining_timeout = max(0.0, (timeout or 0) - elapsed)
                elif not self.is_alive():
                    break

        if len(buffer) == 0:
            return b""

        chunk_size = min(len(buffer), max_bytes)
        result = bytes(buffer[:chunk_size])
        del buffer[:chunk_size]
        return result

    def write(self, data: bytes) -> int:
        """Sends byte data to the SSH channel."""
        if not self._opened:
            raise TransportNotOpenError()
        if self._closed or not self.is_alive():
            raise TransportClosedError("Cannot write to closed or dead SSH transport.")

        assert self._channel is not None
        try:
            total_sent = 0
            while total_sent < len(data):
                sent = self._channel.send(data[total_sent:])
                if sent <= 0:
                    raise TransportClosedError("SSH channel closed during write.")
                total_sent += sent
            return total_sent
        except (socket.error, paramiko.SSHException) as err:
            raise TransportClosedError(f"SSH channel write failed: {err}") from err

    def resize(self, rows: int, cols: int) -> None:
        """Resizes the remote terminal dimensions."""
        if rows <= 0 or cols <= 0:
            raise ValueError("Terminal rows and cols must be positive integers.")
        self._rows = rows
        self._cols = cols
        if self._channel is not None and not self._channel.closed:
            try:
                self._channel.resize_pty(width=cols, height=rows)
            except Exception:
                pass

    def close(self) -> None:
        """Closes channel, underlying SSH client, and joins reader worker."""
        if self._closed:
            return
        self._closed = True

        if self._channel is not None:
            try:
                self._channel.close()
            except Exception:
                pass

        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass

        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=0.5)

    def is_alive(self) -> bool:
        """Returns True if the underlying SSH channel is open and active."""
        if not self._opened or self._closed or self._channel is None:
            return False
        if self._channel.closed:
            return False
        if self._channel.exit_status_ready() and self._stdout_eof:
            return False
        return True
