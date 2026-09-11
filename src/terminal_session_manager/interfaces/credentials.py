"""Credential abstraction and resolution interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from terminal_session_manager.models.credential import CredentialRef


@runtime_checkable
class CredentialResolver(Protocol):
    """Internal contract to resolve secret references safely.

    This interface must only be called by authorized connection adapters.
    Resolved secrets must NEVER be returned to agents, included in logs,
    or stored in events.
    """

    def resolve(self, ref_id: str) -> str | bytes | None:
        """Resolves the raw secret string/bytes for a given credential reference ID."""
        ...

    def get_ref(self, ref_id: str) -> CredentialRef | None:
        """Retrieves only non-sensitive metadata for a credential reference."""
        ...


@runtime_checkable
class ExternalCredentialProvider(Protocol):
    """Contract for delegating credential resolution to an external provider."""

    def resolve_secret(self, ref_id: str) -> str | bytes | None:
        """Resolves secret from external provider. Returns None if not handled."""
        ...

    def get_ref(self, ref_id: str) -> CredentialRef | None:
        """Retrieves metadata from external provider, or None if not handled."""
        ...

