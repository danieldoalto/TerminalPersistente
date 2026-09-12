"""Integration tests for remote SSH Sessions and asynchronous Jobs via DeviceService."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from terminal_session_manager.config import SSHConfig
from terminal_session_manager.errors import DeviceInactiveError, DeviceNotFoundError
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.models.event import EventType
from terminal_session_manager.models.job import JobStatus
from terminal_session_manager.models.session import SessionStatus
from terminal_session_manager.persistence.sqlite import (
    SqliteDeviceRepository,
    SqliteEventRepository,
    SqliteJobRepository,
    SqliteSessionRepository,
    SqliteStorage,
)
from terminal_session_manager.services.credential_store import ProtectedLocalCredentialStore
from terminal_session_manager.services.device_service import DeviceService
from terminal_session_manager.services.job_service import JobService
from terminal_session_manager.services.session_service import SessionService
from terminal_session_manager.transports.ssh import SSHTransport
from tests.test_ssh_transport import MockChannel, MockSSHClient


@pytest.fixture
def tsm_ssh_env():
    """Sets up an in-memory TSM environment with DeviceService, SessionService, and JobService."""
    storage = SqliteStorage(":memory:")
    dev_repo = SqliteDeviceRepository(storage)
    event_repo = SqliteEventRepository(storage)
    session_repo = SqliteSessionRepository(storage)
    job_repo = SqliteJobRepository(storage)

    cred_store = ProtectedLocalCredentialStore(storage, master_key="test-master-key-32-chars-long!!")
    dev_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)

    ssh_cfg = SSHConfig(
        strict_host_key_checking=False,
        connect_timeout=5.0,
    )

    session_service = SessionService(
        session_repo=session_repo,
        event_repo=event_repo,
        device_service=dev_service,
        ssh_config=ssh_cfg,
    )

    job_service = JobService(
        job_repo=job_repo,
        event_repo=event_repo,
        session_repo=session_repo,
        device_service=dev_service,
        ssh_config=ssh_cfg,
    )

    return {
        "storage": storage,
        "dev_service": dev_service,
        "cred_store": cred_store,
        "session_service": session_service,
        "job_service": job_service,
        "event_repo": event_repo,
        "session_repo": session_repo,
        "job_repo": job_repo,
        "ssh_config": ssh_cfg,
    }


def _register_ssh_device(env, name: str, password: str = "secret-pass-99") -> Device:
    """Helper to register a remote SSH device with protected credentials."""
    cred_ref = CredentialRef(name=f"{name}-cred", credential_type=CredentialType.PASSWORD)
    env["cred_store"].save_credential(cred_ref, password)

    device = Device(
        name=name,
        host=f"{name}.infra.internal",
        port=22,
        device_type=DeviceType.SERVER,
        connection_method=ConnectionMethod.SSH,
        default_user="sysadmin",
        credential_ref_id=cred_ref.id,
    )
    return env["dev_service"].register_device(device)


def test_session_creation_with_ssh_device_by_nickname(tsm_ssh_env):
    """Verifies creating an interactive session targeting an SSH device by nickname."""
    env = tsm_ssh_env
    device = _register_ssh_device(env, "db-primary", password="mypassword123")

    mock_client = MockSSHClient()
    with patch("terminal_session_manager.transports.ssh.paramiko.SSHClient", return_value=mock_client):
        local_session = env["session_service"].create_session(
            name="ssh-interactive",
            device_identifier="db-primary",
        )

        assert local_session.session.device_id == device.id
        assert isinstance(local_session.transport, SSHTransport)
        assert local_session.status == SessionStatus.RUNNING

        # Write to session and simulate remote response
        mock_client.mock_channel.feed_stdout(b"postgres=# ")
        read_text = local_session.read_text(timeout=0.2)
        assert "postgres=#" in read_text

        # Send password-containing text to verify redaction
        local_session.write("SELECT 'mypassword123';\n")
        events = env["event_repo"].get_events(local_session.id)
        stdin_events = [e for e in events if e.event_type == EventType.STDIN]
        assert len(stdin_events) == 1
        # Password MUST be redacted in persisted event log
        assert "mypassword123" not in stdin_events[0].payload
        assert "[REDACTED]" in stdin_events[0].payload

        local_session.close()
        assert local_session.status == SessionStatus.CLOSED


def test_job_execution_on_ssh_device_by_nickname(tsm_ssh_env):
    """Verifies asynchronous job execution on a remote SSH host via nickname."""
    env = tsm_ssh_env
    _register_ssh_device(env, "worker-node", password="node-pass-456")

    # Create session bound to worker-node
    mock_client_session = MockSSHClient()
    with patch("terminal_session_manager.transports.ssh.paramiko.SSHClient", return_value=mock_client_session):
        local_session = env["session_service"].create_session(
            name="worker-session",
            device_identifier="worker-node",
        )

    # Submit job to the session
    mock_client_job = MockSSHClient()
    mock_client_job.mock_channel.feed_stdout(b"Disk usage: 45%\nAll checks passed.\n")
    mock_client_job.mock_channel.feed_stderr(b"notice: low priority advisory\n")
    mock_client_job.mock_channel.set_exit_status(0)

    with patch("terminal_session_manager.transports.ssh.paramiko.SSHClient", return_value=mock_client_job):
        job = env["job_service"].submit_job(
            session_id=local_session.id,
            command="df -h && health_check",
            timeout=5.0,
        )

        # Inherited device_id
        assert job.device_id == local_session.session.device_id

        finished_job = env["job_service"].wait_job(job.id, timeout=3.0)
        assert finished_job.status == JobStatus.COMPLETED
        assert finished_job.exit_code == 0
        assert "Disk usage: 45%" in finished_job.stdout
        assert "notice: low priority advisory" in finished_job.stderr

        # Check persisted events
        events = env["event_repo"].get_events(local_session.id)
        stdout_events = [e for e in events if e.event_type == EventType.STDOUT and e.job_id == job.id]
        stderr_events = [e for e in events if e.event_type == EventType.STDERR and e.job_id == job.id]
        assert len(stdout_events) > 0
        assert len(stderr_events) > 0


def test_job_execution_ssh_failure_non_zero_exit_code(tsm_ssh_env):
    """Verifies that non-zero exit code transitions remote job to FAILED."""
    env = tsm_ssh_env
    device = _register_ssh_device(env, "app-srv")

    mock_client_job = MockSSHClient()
    mock_client_job.mock_channel.feed_stderr(b"fatal: command not found\n")
    mock_client_job.mock_channel.set_exit_status(127)

    with patch("terminal_session_manager.transports.ssh.paramiko.SSHClient", return_value=mock_client_job):
        job = env["job_service"].submit_job(
            session_id="dummy-session",
            command="nonexistent_cmd",
            device_id=device.id,
            timeout=3.0,
        )

        finished_job = env["job_service"].wait_job(job.id, timeout=3.0)
        assert finished_job.status == JobStatus.FAILED
        assert finished_job.exit_code == 127
        assert "127" in (finished_job.failure_reason or "")


def test_job_execution_ssh_cancellation(tsm_ssh_env):
    """Verifies cancelling a running SSH job terminates channel cleanly."""
    env = tsm_ssh_env
    device = _register_ssh_device(env, "batch-srv")

    mock_client_job = MockSSHClient()

    with patch("terminal_session_manager.transports.ssh.paramiko.SSHClient", return_value=mock_client_job):
        job = env["job_service"].submit_job(
            session_id="dummy-session",
            command="sleep 100",
            device_id=device.id,
            timeout=10.0,
        )

        time.sleep(0.05)
        cancelled_job = env["job_service"].cancel_job(job.id)
        assert cancelled_job.status == JobStatus.CANCELLED
        assert "Cancelled by user" in (cancelled_job.failure_reason or "")


def test_ssh_device_resolution_errors(tsm_ssh_env):
    """Verifies that non-existent or deactivated SSH devices are rejected."""
    env = tsm_ssh_env
    device = _register_ssh_device(env, "deactivated-srv")
    env["dev_service"].deactivate_device(device.id)

    # Inactive device rejection
    with pytest.raises(DeviceInactiveError):
        env["session_service"].create_session(
            name="fail-session",
            device_identifier="deactivated-srv",
        )

    # Missing device rejection
    with pytest.raises(DeviceNotFoundError):
        env["session_service"].create_session(
            name="fail-session",
            device_identifier="ghost-device",
        )
