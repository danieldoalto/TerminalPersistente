"""Local process terminal transport adapter."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import time
from typing import Sequence

from terminal_session_manager.errors import (
    TransportClosedError,
    TransportError,
    TransportNotOpenError,
    TransportTimeoutError,
)


def _get_default_shell() -> list[str]:
    """Returns platform-appropriate default interactive shell command."""
    if sys.platform == "win32":
        # cmd.exe is universally available and lightweight on all Windows systems
        return ["cmd.exe", "/q"]
    return ["/bin/sh"]


class LocalProcessTransport:
    """TerminalTransport adapter backed by a local OS subprocess.

    Uses non-blocking threaded stream reading to provide reliable timeout
    support and cross-platform compatibility across Windows and POSIX.
    """

    def __init__(
        self,
        command: Sequence[str] | str | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        if command is None:
            self._command: Sequence[str] | str = _get_default_shell()
        else:
            self._command = command

        self._cwd = cwd
        self._env = env
        self._process: subprocess.Popen[bytes] | None = None
        self._reader_thread: threading.Thread | None = None
        self._output_queue: queue.Queue[bytes | None] = queue.Queue()
        self._internal_buffer = bytearray()
        self._closed = False
        self._opened = False
        self._rows = 24
        self._cols = 80
        self._eof_reached = False

    @property
    def exit_code(self) -> int | None:
        """Returns process returncode or None if still running."""
        if self._process is None:
            return None
        return self._process.poll()

    def open(self) -> None:
        """Starts the underlying local process and reader thread."""
        if self._opened:
            return

        try:
            self._process = subprocess.Popen(
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merged terminal output stream
                bufsize=0,
                cwd=self._cwd,
                env=self._env,
            )
        except FileNotFoundError as err:
            raise TransportError(f"Command not found: {self._command}") from err
        except OSError as err:
            raise TransportError(f"Failed to spawn process: {err}") from err

        self._opened = True
        self._closed = False
        self._eof_reached = False

        self._reader_thread = threading.Thread(
            target=self._reader_worker,
            daemon=True,
            name=f"local-transport-reader-{self._process.pid}",
        )
        self._reader_thread.start()

    def _reader_worker(self) -> None:
        """Continuously reads bytes from process stdout pipe into output queue."""
        assert self._process is not None and self._process.stdout is not None
        stdout = self._process.stdout

        try:
            while not self._closed:
                chunk = stdout.read(1024)
                if not chunk:
                    break
                self._output_queue.put(chunk)
        except Exception:
            pass
        finally:
            self._output_queue.put(None)  # EOF marker

    def read(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        """Reads up to max_bytes from the process output stream."""
        if not self._opened:
            raise TransportNotOpenError()

        if max_bytes <= 0:
            return b""

        # Pull available chunks into internal buffer until we have bytes or hit timeout/EOF
        start_time = time.monotonic()
        remaining_timeout = timeout

        while len(self._internal_buffer) == 0 and not self._eof_reached:
            try:
                if remaining_timeout is None:
                    # Blocking read
                    item = self._output_queue.get(timeout=0.2)
                elif remaining_timeout <= 0:
                    item = self._output_queue.get_nowait()
                else:
                    item = self._output_queue.get(timeout=remaining_timeout)

                if item is None:
                    self._eof_reached = True
                    self._output_queue.put(None)  # preserve EOF sentinel
                    break
                self._internal_buffer.extend(item)
            except queue.Empty:
                if remaining_timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed >= (timeout or 0):
                        break
                    remaining_timeout = max(0.0, (timeout or 0) - elapsed)
                elif not self.is_alive():
                    # Process died and no items in queue
                    break

        if len(self._internal_buffer) == 0:
            return b""

        chunk_size = min(len(self._internal_buffer), max_bytes)
        result = bytes(self._internal_buffer[:chunk_size])
        del self._internal_buffer[:chunk_size]
        return result

    def write(self, data: bytes) -> int:
        """Writes byte data to the process stdin channel."""
        if not self._opened:
            raise TransportNotOpenError()
        if self._closed or not self.is_alive():
            raise TransportClosedError("Cannot write to closed or dead process.")

        assert self._process is not None and self._process.stdin is not None
        try:
            self._process.stdin.write(data)
            self._process.stdin.flush()
            return len(data)
        except (BrokenPipeError, OSError) as err:
            raise TransportClosedError("Failed to write to process pipe.") from err

    def resize(self, rows: int, cols: int) -> None:
        """Records terminal dimensions."""
        if rows <= 0 or cols <= 0:
            raise ValueError("Terminal rows and cols must be positive integers.")
        self._rows = rows
        self._cols = cols

    def close(self) -> None:
        """Terminates process cleanly and closes resources."""
        if self._closed:
            return

        self._closed = True

        if self._process is not None:
            # Close stdin first to signal EOF to interactive shells
            if self._process.stdin:
                try:
                    self._process.stdin.close()
                except OSError:
                    pass

            # Terminate process if still running
            if self._process.poll() is None:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=1.0)
                except (subprocess.TimeoutExpired, OSError):
                    try:
                        self._process.kill()
                        self._process.wait(timeout=1.0)
                    except OSError:
                        pass

            if self._process.stdout:
                try:
                    self._process.stdout.close()
                except OSError:
                    pass

        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=0.5)

    def is_alive(self) -> bool:
        """Checks if the underlying process is currently running."""
        if not self._opened or self._closed or self._process is None:
            return False
        return self._process.poll() is None
