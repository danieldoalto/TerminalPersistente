"""Device catalog interface definition."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from terminal_session_manager.models.device import Device


@runtime_checkable
class DeviceRepository(Protocol):
    """Contract for device catalog storage and queries."""

    def register(self, device: Device) -> None:
        """Registers a new device or updates an existing one."""
        ...

    def get_by_id(self, device_id: str) -> Device | None:
        """Retrieves a device by unique ID."""
        ...

    def get_by_name(self, name: str) -> Device | None:
        """Retrieves a device by unique name."""
        ...

    def list_active(self) -> list[Device]:
        """Lists all active registered devices."""
        ...

    def deactivate(self, device_id: str) -> None:
        """Logically deactivates a device by ID."""
        ...
