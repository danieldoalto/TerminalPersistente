"""Tests for centralized configuration loading, environment overrides, and validation."""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from terminal_session_manager.config import (
    ConfigurationError,
    ServerConfig,
    StorageConfig,
    TSMConfig,
    load_config,
    validate_config,
)


def test_default_config_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # Ensure no environment variables interfere
    for key in list(os.environ.keys()):
        if key.startswith("TSM_"):
            monkeypatch.delenv(key, raising=False)

    # Change directory so config.yml in repo root is not loaded by default here
    monkeypatch.chdir(tmp_path)

    config = load_config()
    assert config.server.host == "127.0.0.1"
    assert config.server.port == 8000
    assert config.server.api_token is None
    assert config.storage.db_path == ".tsm/tsm.db"
    assert config.security.require_auth is False
    assert config.sessions.default_read_timeout == 0.5
    assert config.sessions.max_read_bytes == 4096
    assert config.jobs.default_timeout == 60.0
    assert config.jobs.recover_orphaned_on_start is True
    assert config.history.default_event_limit == 50
    assert config.history.max_event_limit == 200


def test_load_from_yaml_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    for key in list(os.environ.keys()):
        if key.startswith("TSM_"):
            monkeypatch.delenv(key, raising=False)

    yaml_file = tmp_path / "custom_config.yml"
    yaml_file.write_text(
        """
server:
  host: "0.0.0.0"
  port: 9000
  api_token: "secret-token-from-file"
storage:
  db_path: "data/custom.db"
security:
  require_auth: true
sessions:
  default_read_timeout: 1.5
  max_read_bytes: 8192
jobs:
  default_timeout: 120.0
  recover_orphaned_on_start: false
history:
  default_event_limit: 25
  max_event_limit: 100
""",
        encoding="utf-8",
    )

    config = load_config(yaml_file)
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 9000
    assert config.server.api_token == "secret-token-from-file"
    assert config.storage.db_path == "data/custom.db"
    assert config.security.require_auth is True
    assert config.sessions.default_read_timeout == 1.5
    assert config.sessions.max_read_bytes == 8192
    assert config.jobs.default_timeout == 120.0
    assert config.jobs.recover_orphaned_on_start is False
    assert config.history.default_event_limit == 25
    assert config.history.max_event_limit == 100


def test_env_var_overrides_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    yaml_file = tmp_path / "test_override.yml"
    yaml_file.write_text(
        """
server:
  host: "127.0.0.1"
  port: 8080
storage:
  db_path: "data/yaml.db"
""",
        encoding="utf-8",
    )

    # Set environment variables that should override YAML
    monkeypatch.setenv("TSM_SERVER_PORT", "9999")
    monkeypatch.setenv("TSM_SERVER_HOST", "192.168.1.10")
    monkeypatch.setenv("TSM_DB_PATH", "env/override.db")
    monkeypatch.setenv("TSM_API_TOKEN", "env-token-override")
    monkeypatch.setenv("TSM_MASTER_KEY", "env-master-key")
    monkeypatch.setenv("TSM_REQUIRE_AUTH", "true")

    config = load_config(yaml_file)
    assert config.server.port == 9999
    assert config.server.host == "192.168.1.10"
    assert config.storage.db_path == "env/override.db"
    assert config.server.api_token == "env-token-override"
    assert config.security.master_key == "env-master-key"
    assert config.security.require_auth is True


def test_validation_invalid_ports():
    with pytest.raises(ConfigurationError, match="Invalid server port"):
        cfg = TSMConfig(server=ServerConfig(port=0))
        validate_config(cfg)

    with pytest.raises(ConfigurationError, match="Invalid server port"):
        cfg = TSMConfig(server=ServerConfig(port=70000))
        validate_config(cfg)


def test_validation_invalid_host():
    with pytest.raises(ConfigurationError, match="host address cannot be empty"):
        cfg = TSMConfig(server=ServerConfig(host="   "))
        validate_config(cfg)


def test_validation_invalid_db_path():
    with pytest.raises(ConfigurationError, match="db_path cannot be empty"):
        cfg = TSMConfig(storage=StorageConfig(db_path=""))
        validate_config(cfg)


def test_validation_require_auth_missing_token():
    cfg = TSMConfig()
    cfg.security.require_auth = True
    cfg.server.api_token = None
    with pytest.raises(ConfigurationError, match="Authentication is required"):
        validate_config(cfg)

    cfg.server.api_token = "   "
    with pytest.raises(ConfigurationError, match="Authentication is required"):
        validate_config(cfg)


def test_validation_invalid_timeouts():
    cfg = TSMConfig()
    cfg.sessions.default_read_timeout = 0
    with pytest.raises(ConfigurationError, match="sessions.default_read_timeout must be greater than 0"):
        validate_config(cfg)

    cfg2 = TSMConfig()
    cfg2.jobs.default_timeout = -5.0
    with pytest.raises(ConfigurationError, match="jobs.default_timeout must be greater than 0"):
        validate_config(cfg2)


def test_validation_invalid_limits():
    cfg = TSMConfig()
    cfg.history.default_event_limit = 0
    with pytest.raises(ConfigurationError, match="history.default_event_limit must be at least 1"):
        validate_config(cfg)

    cfg2 = TSMConfig()
    cfg2.history.default_event_limit = 100
    cfg2.history.max_event_limit = 50
    with pytest.raises(ConfigurationError, match="history.max_event_limit"):
        validate_config(cfg2)
