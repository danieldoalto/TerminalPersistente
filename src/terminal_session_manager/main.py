"""Executable CLI entry point for Terminal Session Manager."""

from __future__ import annotations

import argparse
import sys

from terminal_session_manager import __version__
from terminal_session_manager.app import TSMApplication
from terminal_session_manager.config import ConfigurationError, load_config


def main(argv: list[str] | None = None) -> int:
    """CLI entry point dispatching subcommands and lifecycle execution."""
    parser = argparse.ArgumentParser(
        prog="terminal-session-manager",
        description="Terminal Session Manager — Minimalist persistent terminal architecture for agents.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"terminal-session-manager {__version__}")
    parser.add_argument("--config", dest="config_path", help="Path to custom config.yml configuration file.")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # validate
    subparsers.add_parser("validate", help="Validates configuration and storage setup.")

    # api
    subparsers.add_parser("api", help="Starts the HTTP REST API server.")

    # mcp
    subparsers.add_parser("mcp", help="Starts the FastMCP Model Context Protocol server.")

    # status
    subparsers.add_parser("status", help="Displays current configuration and system overview.")

    parsed = parser.parse_args(argv if argv is not None else sys.argv[1:])

    # Default to status if no subcommand provided
    command = parsed.command or "status"

    try:
        config = load_config(parsed.config_path)
    except ConfigurationError as err:
        print(f"Configuration error: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"Unexpected error loading configuration: {err}", file=sys.stderr)
        return 1

    if command == "validate":
        print("Configuration OK.")
        print(f"  - Server: {config.server.host}:{config.server.port} (require_auth={config.security.require_auth})")
        print(f"  - Storage: {config.storage.db_path}")
        print(f"  - Sessions: read_timeout={config.sessions.default_read_timeout}s, max_bytes={config.sessions.max_read_bytes}")
        print(f"  - Jobs: timeout={config.jobs.default_timeout}s, recover_orphans={config.jobs.recover_orphaned_on_start}")
        print(f"  - History: default_limit={config.history.default_event_limit}, max_limit={config.history.max_event_limit}")
        return 0

    if command == "api":
        app = TSMApplication(config)
        reconciled = app.startup()
        print(f"Starting TSM API Server on {config.server.base_url if hasattr(config.server, 'base_url') else f'http://{config.server.host}:{config.server.port}'} ...")
        if reconciled["recovered_jobs"] > 0 or reconciled["recovered_sessions"] > 0:
            print(f"Startup reconciliation: {reconciled['recovered_jobs']} jobs and {reconciled['recovered_sessions']} sessions recovered.")
        api_server = app.create_api_server()
        try:
            api_server.start()
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
        finally:
            api_server.stop()
            app.shutdown()
        return 0

    if command == "mcp":
        app = TSMApplication(config)
        reconciled = app.startup()
        mcp_server = app.create_mcp_server()
        mcp_server.run(transport="stdio")
        return 0

    # Default overview / status
    print("=" * 60)
    print(f"Terminal Session Manager v{__version__}")
    print("=" * 60)
    print("Status: Configuração válida e serviços operacionais.")
    print(f"  - Host/Porta HTTP: {config.server.host}:{config.server.port}")
    print(f"  - Banco de Dados: {config.storage.db_path}")
    print(f"  - Autenticação obrigatória: {config.security.require_auth}")
    print("\nComandos disponíveis:")
    print("  terminal-session-manager api       -> Inicia a API HTTP")
    print("  terminal-session-manager mcp       -> Inicia o servidor FastMCP (stdio)")
    print("  terminal-session-manager validate  -> Valida a configuração")
    print("  uv run pytest                      -> Executa a suíte de testes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
