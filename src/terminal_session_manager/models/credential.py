"""Credential reference model ensuring secret isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from terminal_session_manager.errors import ValidationError


class CredentialType(str, Enum):
    """Supported types of credentials."""

    PASSWORD = "password"
    SSH_KEY = "ssh_key"
    TOKEN = "token"
    CERTIFICATE = "certificate"


@dataclass
class CredentialRef:
    """Safe reference metadata for credentials.

    NOTE: This model strictly avoids storing or exposing plaintext secrets,
    ensuring security policies and preventing leaks to agents or logs.
    """

    name: str
    credential_type: CredentialType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("CredentialRef ID cannot be empty.")
        if not self.name:
            raise ValidationError("CredentialRef name cannot be empty.")
        if not isinstance(self.credential_type, CredentialType):
            try:
                self.credential_type = CredentialType(self.credential_type)
            except ValueError as err:
                raise ValidationError(
                    f"Invalid credential type: {self.credential_type}"
                ) from err
