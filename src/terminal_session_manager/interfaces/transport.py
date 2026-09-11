"""Terminal and transport adapter interfaces."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TerminalTransport(Protocol):
    """Contract for low-level terminal/transport implementations (PTY, SSH, Serial, etc.)."""

    def open(self) -> None:
        """Initializes and opens the underlying transport channel."""
        ...

    def read(self, max_bytes: int = 4096, timeout: float | None = None) -> bytes:
        """Reads up to max_bytes from the transport."""
        ...

    def write(self, data: bytes) -> int:
        """Writes raw byte data to the transport channel and returns bytes written."""
        ...

    def resize(self, rows: int, cols: int) -> None:
        """Resizes the terminal dimensions if supported by the transport."""
        ...

    def close(self) -> None:
        """Closes the transport channel cleanly."""
        ...

    def is_alive(self) -> bool:
        """Checks if the underlying process/connection is currently active."""
        ...
