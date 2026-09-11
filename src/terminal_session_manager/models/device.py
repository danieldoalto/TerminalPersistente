"""Device inventory model and connection metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from terminal_session_manager.errors import ValidationError


class DeviceType(str, Enum):
    """Categorization of managed devices."""

    SERVER = "server"
    ROUTER = "router"
    SWITCH = "switch"
    CONTAINER = "container"
    WORKSTATION = "workstation"
    GENERIC = "generic"


class ConnectionMethod(str, Enum):
    """Supported transport/connection mechanisms for devices."""

    LOCAL = "local"
    SSH = "ssh"
    SERIAL = "serial"
    TELNET = "telnet"


@dataclass
class Device:
    """Represents an addressable device in the inventory."""

    name: str
    host: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    port: int = 22
    device_type: DeviceType = DeviceType.SERVER
    connection_method: ConnectionMethod = ConnectionMethod.SSH
    default_user: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
    credential_ref_id: str | None = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("Device ID cannot be empty.")
        if not self.name.strip():
            raise ValidationError("Device name cannot be empty.")
        if not self.host.strip():
            raise ValidationError("Device host cannot be empty.")
        if not (1 <= self.port <= 65535):
            raise ValidationError(f"Invalid port number: {self.port}. Must be between 1 and 65535.")

        if not isinstance(self.device_type, DeviceType):
            try:
                self.device_type = DeviceType(self.device_type)
            except ValueError as err:
                raise ValidationError(f"Invalid device type: {self.device_type}") from err

        if not isinstance(self.connection_method, ConnectionMethod):
            try:
                self.connection_method = ConnectionMethod(self.connection_method)
            except ValueError as err:
                raise ValidationError(
                    f"Invalid connection method: {self.connection_method}"
                ) from err

    def deactivate(self) -> None:
        """Deactivates device logically without deleting historical references."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def remove(self) -> None:
        """Marks device as logically removed without deleting historical references."""
        self.is_deleted = True
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

