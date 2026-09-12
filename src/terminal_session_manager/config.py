"""Centralized configuration loading, validation, and environment overrides for TSM."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any
import yaml

from terminal_session_manager.errors import DomainError


class ConfigurationError(DomainError):
    """Raised when configuration values are missing, invalid, or conflicting."""


@dataclass
class ServerConfig:
    """HTTP API server network and authorization parameters."""

    host: str = "127.0.0.1"
    port: int = 8000
    api_token: str | None = None


@dataclass
class StorageConfig:
    """Durability and database persistence parameters."""

    db_path: str = ".tsm/tsm.db"


@dataclass
class SecurityConfig:
    """Cryptography, credential protection, and authorization policies."""

    master_key: str | bytes | None = None
    require_auth: bool = False


@dataclass
class SessionsConfig:
    """Interactive terminal session constraints."""

    default_read_timeout: float = 0.5
    max_read_bytes: int = 4096
    cleanup_on_shutdown: bool = True


@dataclass
class JobsConfig:
    """Asynchronous job execution policies."""

    default_timeout: float = 60.0
    recover_orphaned_on_start: bool = True


@dataclass
class HistoryConfig:
    """Event streaming, ordering, and pagination limits."""

    default_event_limit: int = 50
    max_event_limit: int = 200


@dataclass
class SSHConfig:
    """SSH transport connection and host key verification settings."""

    known_hosts_path: str | None = None
    strict_host_key_checking: bool = True
    connect_timeout: float = 10.0
    default_port: int = 22


@dataclass
class TSMConfig:
    """Aggregated configuration root for Terminal Session Manager."""

    server: ServerConfig = field(default_factory=ServerConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    sessions: SessionsConfig = field(default_factory=SessionsConfig)
    jobs: JobsConfig = field(default_factory=JobsConfig)
    history: HistoryConfig = field(default_factory=HistoryConfig)
    ssh: SSHConfig = field(default_factory=SSHConfig)


def validate_config(config: TSMConfig) -> None:
    """Enforces correctness constraints and security invariants on configuration."""
    # Server validations
    if not (1 <= config.server.port <= 65535):
        raise ConfigurationError(
            f"Invalid server port: {config.server.port}. Port must be between 1 and 65535."
        )
    if not config.server.host or not config.server.host.strip():
        raise ConfigurationError("Server host address cannot be empty.")

    # Storage validations
    if not config.storage.db_path or not config.storage.db_path.strip():
        raise ConfigurationError("Storage db_path cannot be empty.")

    # Security validations
    if config.security.require_auth:
        if not config.server.api_token or not config.server.api_token.strip():
            raise ConfigurationError(
                "Authentication is required (require_auth=True), but api_token is empty or unset."
            )

    # Sessions validations
    if config.sessions.default_read_timeout <= 0:
        raise ConfigurationError("sessions.default_read_timeout must be greater than 0.")
    if config.sessions.max_read_bytes <= 0:
        raise ConfigurationError("sessions.max_read_bytes must be greater than 0.")

    # Jobs validations
    if config.jobs.default_timeout <= 0:
        raise ConfigurationError("jobs.default_timeout must be greater than 0.")

    # History validations
    if config.history.default_event_limit < 1:
        raise ConfigurationError("history.default_event_limit must be at least 1.")
    if config.history.max_event_limit < config.history.default_event_limit:
        raise ConfigurationError(
            f"history.max_event_limit ({config.history.max_event_limit}) cannot be smaller than "
            f"default_event_limit ({config.history.default_event_limit})."
        )

    # SSH validations
    if not (1 <= config.ssh.default_port <= 65535):
        raise ConfigurationError(
            f"Invalid ssh.default_port: {config.ssh.default_port}. Must be between 1 and 65535."
        )
    if config.ssh.connect_timeout <= 0:
        raise ConfigurationError(
            f"Invalid ssh.connect_timeout: {config.ssh.connect_timeout}. Must be positive."
        )


def _parse_bool(val: Any) -> bool:
    """Converts common boolean string representations to boolean."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "on", "t")
    return False


def load_config(config_path: str | Path | None = None) -> TSMConfig:
    """Loads configuration from defaults, YAML file, and environment overrides.

    Precedence order (highest to lowest):
      1. Environment variables (TSM_*)
      2. YAML configuration file (config.yml or specified path)
      3. Secure built-in defaults

    Args:
        config_path: Path to configuration file. If None, checks TSM_CONFIG_PATH,
                     then searches for config.yml in the current working directory.
    """
    config = TSMConfig()

    # Determine file location
    target_file: Path | None = None
    if config_path is not None:
        target_file = Path(config_path)
    elif "TSM_CONFIG_PATH" in os.environ:
        target_file = Path(os.environ["TSM_CONFIG_PATH"])
    elif Path("config.yml").is_file():
        target_file = Path("config.yml")

    # 1. Parse YAML if file exists
    if target_file is not None and target_file.is_file():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as err:
            raise ConfigurationError(f"Failed to read configuration file '{target_file}': {err}") from err

        if not isinstance(data, dict):
            raise ConfigurationError(f"Invalid YAML structure in '{target_file}': must be a dictionary.")

        # Server section
        server_data = data.get("server", {})
        if isinstance(server_data, dict):
            if "host" in server_data:
                config.server.host = str(server_data["host"])
            if "port" in server_data:
                try:
                    config.server.port = int(server_data["port"])
                except (ValueError, TypeError) as err:
                    raise ConfigurationError(f"Invalid port in config file: {server_data['port']}") from err
            if "api_token" in server_data and server_data["api_token"] is not None:
                config.server.api_token = str(server_data["api_token"]) if server_data["api_token"] != "" else None

        # Storage section
        storage_data = data.get("storage", {})
        if isinstance(storage_data, dict):
            if "db_path" in storage_data:
                config.storage.db_path = str(storage_data["db_path"])

        # Security section
        security_data = data.get("security", {})
        if isinstance(security_data, dict):
            if "require_auth" in security_data:
                config.security.require_auth = _parse_bool(security_data["require_auth"])
            # Note: raw secrets must NOT be committed in YAML, but if test specifies master_key it's respected
            if "master_key" in security_data and security_data["master_key"]:
                config.security.master_key = security_data["master_key"]

        # Sessions section
        sessions_data = data.get("sessions", {})
        if isinstance(sessions_data, dict):
            if "default_read_timeout" in sessions_data:
                config.sessions.default_read_timeout = float(sessions_data["default_read_timeout"])
            if "max_read_bytes" in sessions_data:
                config.sessions.max_read_bytes = int(sessions_data["max_read_bytes"])
            if "cleanup_on_shutdown" in sessions_data:
                config.sessions.cleanup_on_shutdown = _parse_bool(sessions_data["cleanup_on_shutdown"])

        # Jobs section
        jobs_data = data.get("jobs", {})
        if isinstance(jobs_data, dict):
            if "default_timeout" in jobs_data:
                config.jobs.default_timeout = float(jobs_data["default_timeout"])
            if "recover_orphaned_on_start" in jobs_data:
                config.jobs.recover_orphaned_on_start = _parse_bool(jobs_data["recover_orphaned_on_start"])

        # History section
        history_data = data.get("history", {})
        if isinstance(history_data, dict):
            if "default_event_limit" in history_data:
                config.history.default_event_limit = int(history_data["default_event_limit"])
            if "max_event_limit" in history_data:
                config.history.max_event_limit = int(history_data["max_event_limit"])

        # SSH section
        ssh_data = data.get("ssh", {})
        if isinstance(ssh_data, dict):
            if "known_hosts_path" in ssh_data and ssh_data["known_hosts_path"]:
                config.ssh.known_hosts_path = str(ssh_data["known_hosts_path"])
            if "strict_host_key_checking" in ssh_data:
                config.ssh.strict_host_key_checking = _parse_bool(ssh_data["strict_host_key_checking"])
            if "connect_timeout" in ssh_data:
                config.ssh.connect_timeout = float(ssh_data["connect_timeout"])
            if "default_port" in ssh_data:
                config.ssh.default_port = int(ssh_data["default_port"])

    # 2. Apply environment variable overrides (highest precedence)
    if "TSM_SERVER_HOST" in os.environ:
        config.server.host = os.environ["TSM_SERVER_HOST"]

    if "TSM_SERVER_PORT" in os.environ:
        try:
            config.server.port = int(os.environ["TSM_SERVER_PORT"])
        except ValueError as err:
            raise ConfigurationError(
                f"Invalid TSM_SERVER_PORT value: {os.environ['TSM_SERVER_PORT']}. Must be integer."
            ) from err

    if "TSM_API_TOKEN" in os.environ:
        token_val = os.environ["TSM_API_TOKEN"].strip()
        config.server.api_token = token_val if token_val else None

    if "TSM_DB_PATH" in os.environ:
        config.storage.db_path = os.environ["TSM_DB_PATH"]

    if "TSM_MASTER_KEY" in os.environ:
        config.security.master_key = os.environ["TSM_MASTER_KEY"]

    if "TSM_REQUIRE_AUTH" in os.environ:
        config.security.require_auth = _parse_bool(os.environ["TSM_REQUIRE_AUTH"])

    if "TSM_SSH_KNOWN_HOSTS" in os.environ:
        config.ssh.known_hosts_path = os.environ["TSM_SSH_KNOWN_HOSTS"]

    if "TSM_SSH_STRICT_HOST_KEY_CHECKING" in os.environ:
        config.ssh.strict_host_key_checking = _parse_bool(os.environ["TSM_SSH_STRICT_HOST_KEY_CHECKING"])

    if "TSM_SSH_CONNECT_TIMEOUT" in os.environ:
        try:
            config.ssh.connect_timeout = float(os.environ["TSM_SSH_CONNECT_TIMEOUT"])
        except ValueError as err:
            raise ConfigurationError(
                f"Invalid TSM_SSH_CONNECT_TIMEOUT value: {os.environ['TSM_SSH_CONNECT_TIMEOUT']}. Must be float."
            ) from err

    if "TSM_SSH_DEFAULT_PORT" in os.environ:
        try:
            config.ssh.default_port = int(os.environ["TSM_SSH_DEFAULT_PORT"])
        except ValueError as err:
            raise ConfigurationError(
                f"Invalid TSM_SSH_DEFAULT_PORT value: {os.environ['TSM_SSH_DEFAULT_PORT']}. Must be integer."
            ) from err

    # 3. Validate final consolidated configuration
    validate_config(config)

    return config
