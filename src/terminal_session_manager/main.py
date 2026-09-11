"""Executable entry point for Terminal Session Manager."""

from __future__ import annotations

import sys

from terminal_session_manager import __version__


def main(argv: list[str] | None = None) -> int:
    """CLI entry point displaying version and skeleton status."""
    args = argv if argv is not None else sys.argv[1:]
    if "--version" in args or "-v" in args:
        print(f"terminal-session-manager {__version__}")
        return 0

    print("=" * 60)
    print(f"Terminal Session Manager v{__version__} [Etapa 2 - Persistência e Histórico]")
    print("=" * 60)
    print("Status: Esqueleto executável, contratos, transporte local e persistência SQLite carregados.")
    print("Módulos disponíveis:")
    print("  - terminal_session_manager.models (Session, Job, Device, CredentialRef, Event)")
    print("  - terminal_session_manager.interfaces (Persistence, Transport, Device, Credentials)")
    print("  - terminal_session_manager.transports (LocalProcessTransport)")
    print("  - terminal_session_manager.services (LocalSession)")
    print("  - terminal_session_manager.persistence (SqliteSessionRepository, SqliteJobRepository, SqliteEventRepository)")
    print("  - terminal_session_manager.errors (DomainError, TransportError, ...)")
    print("Execute a suíte de testes com: uv run pytest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
