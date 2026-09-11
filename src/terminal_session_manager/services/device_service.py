"""Device catalog and safe internal connection resolution service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from terminal_session_manager.errors import (
    CredentialNotFoundError,
    DeviceInactiveError,
    DeviceNotFoundError,
    ValidationError,
)
from terminal_session_manager.interfaces.credentials import CredentialResolver
from terminal_session_manager.interfaces.device import DeviceRepository
from terminal_session_manager.models.credential import CredentialRef
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType


@dataclass(frozen=True)
class ResolvedConnection:
    """Internal connection metadata container.

    NOTE: The resolved secret exists strictly in memory and is utilized solely
    by transport adapters. It MUST NEVER be returned to agents or persisted in logs.
    """

    device_id: str
    device_name: str
    host: str
    port: int
    connection_method: ConnectionMethod
    default_user: str | None
    credential_ref: CredentialRef | None
    secret: str | bytes | None
    options: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        secret_repr = "[PROTECTED]" if self.secret is not None else "None"
        return (
            f"ResolvedConnection(device_id='{self.device_id}', device_name='{self.device_name}', "
            f"host='{self.host}', port={self.port}, method='{self.connection_method.value}', "
            f"user={self.default_user!r}, secret={secret_repr})"
        )


class DeviceService:
    """Manages the device inventory and handles secure connection resolution."""

    def __init__(
        self,
        repository: DeviceRepository,
        credential_resolver: CredentialResolver | None = None,
    ) -> None:
        self.repository = repository
        self.credential_resolver = credential_resolver

    def register_device(self, device: Device) -> Device:
        """Registers a new device or updates an existing one."""
        self.repository.register(device)
        return device

    def create_device(
        self,
        name: str,
        host: str,
        port: int = 22,
        device_type: DeviceType = DeviceType.SERVER,
        connection_method: ConnectionMethod = ConnectionMethod.SSH,
        default_user: str | None = None,
        options: dict[str, Any] | None = None,
        credential_ref_id: str | None = None,
    ) -> Device:
        """Creates, persists, and returns a new Device."""
        device = Device(
            name=name,
            host=host,
            port=port,
            device_type=device_type,
            connection_method=connection_method,
            default_user=default_user,
            options=options or {},
            credential_ref_id=credential_ref_id,
        )
        self.repository.register(device)
        return device

    def get_device(self, device_id: str) -> Device | None:
        """Retrieves a device by ID."""
        return self.repository.get_by_id(device_id)

    def get_device_by_name(self, name: str) -> Device | None:
        """Retrieves a device by unique name/nickname."""
        return self.repository.get_by_name(name)

    def update_device(
        self,
        device_id: str,
        name: str | None = None,
        host: str | None = None,
        port: int | None = None,
        device_type: DeviceType | None = None,
        connection_method: ConnectionMethod | None = None,
        default_user: str | None = None,
        options: dict[str, Any] | None = None,
        credential_ref_id: str | None = None,
        is_active: bool | None = None,
    ) -> Device:
        """Updates attributes of an existing device."""
        device = self.repository.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)

        if name is not None:
            device.name = name
        if host is not None:
            device.host = host
        if port is not None:
            device.port = port
        if device_type is not None:
            device.device_type = device_type
        if connection_method is not None:
            device.connection_method = connection_method
        if default_user is not None:
            device.default_user = default_user
        if options is not None:
            device.options = options
        if credential_ref_id is not None:
            device.credential_ref_id = credential_ref_id
        if is_active is not None:
            device.is_active = is_active

        device.updated_at = datetime.now(timezone.utc)
        device.__post_init__()
        self.repository.register(device)
        return device

    def deactivate_device(self, device_id: str) -> Device:
        """Deactivates a device logically."""
        device = self.repository.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)

        device.deactivate()
        self.repository.register(device)
        return device

    def remove_device(self, device_id: str) -> Device:
        """Logically marks a device as removed."""
        device = self.repository.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)

        device.remove()
        self.repository.register(device)
        return device

    def list_devices(self, only_active: bool = True) -> list[Device]:
        """Lists registered devices."""
        if only_active:
            return self.repository.list_active()
        return self.repository.list_all(include_deleted=False)

    def resolve_connection(self, name_or_id: str) -> ResolvedConnection:
        """Resolves full connection details internally using a name or device ID.

        Enforces that deactivated or removed devices cannot be used, and resolves
        the configured secret in memory without leaking it to the caller.
        """
        device = self.repository.get_by_name(name_or_id)
        if device is None:
            device = self.repository.get_by_id(name_or_id)

        if device is None:
            raise DeviceNotFoundError(name_or_id)

        if device.is_deleted or not device.is_active:
            raise DeviceInactiveError(name_or_id)

        cred_ref: CredentialRef | None = None
        secret: str | bytes | None = None

        if device.credential_ref_id:
            if self.credential_resolver is None:
                raise CredentialNotFoundError(device.credential_ref_id)

            cred_ref = self.credential_resolver.get_ref(device.credential_ref_id)
            secret = self.credential_resolver.resolve(device.credential_ref_id)
            if secret is None:
                raise CredentialNotFoundError(device.credential_ref_id)

        return ResolvedConnection(
            device_id=device.id,
            device_name=device.name,
            host=device.host,
            port=device.port,
            connection_method=device.connection_method,
            default_user=device.default_user,
            credential_ref=cred_ref,
            secret=secret,
            options=dict(device.options),
        )
