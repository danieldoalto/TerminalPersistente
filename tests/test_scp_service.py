"""Unit and integration tests for SCP file transfer service."""

from __future__ import annotations

from pathlib import Path
import socket
import threading
import time
from typing import Any

import paramiko
import pytest

from terminal_session_manager.config import SSHConfig
from terminal_session_manager.errors import (
    DeviceInactiveError,
    DeviceNotFoundError,
    ValidationError,
)
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.models.event import EventType
from terminal_session_manager.models.job import Job, JobStatus
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
from terminal_session_manager.services.scp_service import SCPService, SCPTransferDirection
from tests.test_ssh_transport import MockChannel, MockSSHClient


class MockSCPClient:
    """Simulates scp.SCPClient operations in memory with progress callbacks."""

    def __init__(
        self,
        transport: Any,
        socket_timeout: float | None = None,
        progress: Any | None = None,
        sanitize: Any | None = None,
    ) -> None:
        self.transport = transport
        self.socket_timeout = socket_timeout
        self.progress = progress
        self.sanitize = sanitize
        self.put_calls: list[tuple[str, str]] = []
        self.get_calls: list[tuple[str, str]] = []
        self.closed = False
        self.should_timeout = False

    def put(self, local_path: str, remote_path: str = ".") -> None:
        if self.should_timeout:
            raise socket.timeout("SCP put operation timed out")
        self.put_calls.append((local_path, remote_path))
        p = Path(local_path)
        size = p.stat().st_size if p.exists() else 42
        if self.progress:
            self.progress(p.name, size, size)

    def get(self, remote_path: str, local_path: str = "") -> None:
        if self.should_timeout:
            raise socket.timeout("SCP get operation timed out")
        self.get_calls.append((remote_path, local_path))
        dest = Path(local_path)
        if dest.is_dir():
            dest_file = dest / Path(remote_path).name
        else:
            dest_file = dest
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        dest_file.write_text("mock remote file content", encoding="utf-8")
        size = len(b"mock remote file content")
        if self.progress:
            self.progress(Path(remote_path).name, size, size)

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def scp_env(tmp_path: Path):
    """Sets up an isolated in-memory test environment for SCP transfers."""
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

    active_mock_clients: list[MockSSHClient] = []
    active_mock_scps: list[MockSCPClient] = []

    def mock_client_factory():
        client = MockSSHClient()
        active_mock_clients.append(client)
        return client

    def mock_scp_factory(transport, **kwargs):
        scp_cli = MockSCPClient(transport, **kwargs)
        active_mock_scps.append(scp_cli)
        return scp_cli

    scp_service = SCPService(
        device_service=dev_service,
        job_repo=job_repo,
        event_repo=event_repo,
        session_repo=session_repo,
        ssh_config=ssh_cfg,
        client_factory=mock_client_factory,
        scp_factory=mock_scp_factory,
    )

    job_service = JobService(
        job_repo=job_repo,
        event_repo=event_repo,
        session_repo=session_repo,
        device_service=dev_service,
        ssh_config=ssh_cfg,
        scp_service=scp_service,
    )

    # Register an SSH device with password
    cred = CredentialRef(name="srv-pass", credential_type=CredentialType.PASSWORD)
    cred_store.save_credential(cred, "super-secret-password-xyz")

    device = Device(
        name="srv-remote",
        host="192.168.1.100",
        port=22,
        device_type=DeviceType.SERVER,
        connection_method=ConnectionMethod.SSH,
        default_user="admin",
        credential_ref_id=cred.id,
    )
    dev_service.register_device(device)

    return {
        "scp_service": scp_service,
        "job_service": job_service,
        "dev_service": dev_service,
        "event_repo": event_repo,
        "job_repo": job_repo,
        "cred_store": cred_store,
        "device": device,
        "tmp_path": tmp_path,
        "mock_clients": active_mock_clients,
        "mock_scps": active_mock_scps,
    }


def test_scp_upload_success(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]

    # Create local file
    local_file = tmp_path / "deploy.tar.gz"
    local_file.write_text("package payload data 12345", encoding="utf-8")

    job = service.submit_transfer(
        device_identifier="srv-remote",
        direction="upload",
        local_path=local_file,
        remote_path="/var/www/deploy.tar.gz",
    )

    assert job.status in (JobStatus.CREATED, JobStatus.RUNNING)
    finished = service.wait_transfer(job.id, timeout=3.0)

    assert finished.status == JobStatus.COMPLETED
    assert finished.exit_code == 0
    assert "Successfully uploaded" in finished.stdout
    assert finished.metadata["transferred_bytes"] == len(b"package payload data 12345")
    assert finished.metadata["direction"] == "upload"

    # Verify mock was called
    mock_scps = scp_env["mock_scps"]
    assert len(mock_scps) == 1
    assert mock_scps[0].put_calls == [(str(local_file.resolve()), "/var/www/deploy.tar.gz")]

    # Verify audit events
    events = scp_env["event_repo"].get_events(finished.session_id)
    event_types = [e.event_type for e in events]
    assert EventType.STATE_CHANGE in event_types
    assert EventType.STDOUT in event_types


def test_scp_download_success(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]

    dest_file = tmp_path / "downloaded_config.json"

    job = service.submit_transfer(
        device_identifier="srv-remote",
        direction=SCPTransferDirection.DOWNLOAD,
        remote_path="/etc/app/config.json",
        local_path=dest_file,
    )

    finished = service.wait_transfer(job.id, timeout=3.0)

    assert finished.status == JobStatus.COMPLETED
    assert finished.exit_code == 0
    assert "Successfully downloaded" in finished.stdout
    assert dest_file.is_file()
    assert dest_file.read_text(encoding="utf-8") == "mock remote file content"


def test_scp_device_nickname_resolution(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]

    local_file = tmp_path / "notes.txt"
    local_file.write_text("notes", encoding="utf-8")

    job = service.submit_transfer(
        device_identifier="srv-remote",
        direction="upload",
        local_path=local_file,
        remote_path="/tmp/notes.txt",
    )
    finished = service.wait_transfer(job.id, timeout=3.0)
    assert finished.device_id == scp_env["device"].id


def test_scp_upload_file_not_found(scp_env):
    service = scp_env["scp_service"]
    non_existent = scp_env["tmp_path"] / "non_existent_file.xyz"

    with pytest.raises(ValidationError, match="Local file does not exist"):
        service.submit_transfer(
            device_identifier="srv-remote",
            direction="upload",
            local_path=non_existent,
            remote_path="/remote/path",
        )


def test_scp_download_invalid_destination_dir(scp_env):
    service = scp_env["scp_service"]
    bad_dir_path = scp_env["tmp_path"] / "non_existent_folder_abc" / "dest.txt"

    with pytest.raises(ValidationError, match="Destination directory does not exist"):
        service.submit_transfer(
            device_identifier="srv-remote",
            direction="download",
            remote_path="/remote/file.txt",
            local_path=bad_dir_path,
        )


def test_scp_inactive_device(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]
    local_file = tmp_path / "file.txt"
    local_file.write_text("abc", encoding="utf-8")

    scp_env["dev_service"].deactivate_device(scp_env["device"].id)

    with pytest.raises(DeviceInactiveError):
        service.submit_transfer(
            device_identifier="srv-remote",
            direction="upload",
            local_path=local_file,
            remote_path="/tmp/file.txt",
        )


def test_scp_non_existent_device(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]
    local_file = tmp_path / "file.txt"
    local_file.write_text("abc", encoding="utf-8")

    with pytest.raises(DeviceNotFoundError):
        service.submit_transfer(
            device_identifier="unknown-ghost-device",
            direction="upload",
            local_path=local_file,
            remote_path="/tmp/file.txt",
        )


def test_scp_non_ssh_device(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]
    local_file = tmp_path / "file.txt"
    local_file.write_text("abc", encoding="utf-8")

    local_dev = Device(
        name="local-box",
        host="localhost",
        connection_method=ConnectionMethod.LOCAL,
    )
    scp_env["dev_service"].register_device(local_dev)

    with pytest.raises(ValidationError, match="require ConnectionMethod.SSH"):
        service.submit_transfer(
            device_identifier="local-box",
            direction="upload",
            local_path=local_file,
            remote_path="/tmp/file.txt",
        )


def test_scp_auth_failure_masks_secret(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]
    local_file = tmp_path / "file.txt"
    local_file.write_text("abc", encoding="utf-8")

    # Injeta mock com erro de autenticação contendo a senha secreta
    def failing_client_factory():
        cli = MockSSHClient()
        def fail_connect(**kwargs):
            raise paramiko.AuthenticationException("Failed authentication using password super-secret-password-xyz")
        cli.connect = fail_connect
        return cli

    service.client_factory = failing_client_factory

    job = service.submit_transfer(
        device_identifier="srv-remote",
        direction="upload",
        local_path=local_file,
        remote_path="/tmp/file.txt",
    )
    finished = service.wait_transfer(job.id, timeout=3.0)

    assert finished.status == JobStatus.FAILED
    assert finished.exit_code == 1
    # Garante que a senha foi mascarada para [REDACTED]
    assert "super-secret-password-xyz" not in finished.failure_reason
    assert "[REDACTED]" in finished.failure_reason
    assert "super-secret-password-xyz" not in finished.stderr
    assert "[REDACTED]" in finished.stderr

    # Garante que nenhum evento gravou o segredo em texto puro
    events = scp_env["event_repo"].get_events(finished.session_id)
    for ev in events:
        ev_str = str(ev.payload)
        assert "super-secret-password-xyz" not in ev_str


def test_scp_transfer_timeout(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]
    local_file = tmp_path / "file.txt"
    local_file.write_text("abc", encoding="utf-8")

    def timeout_scp_factory(transport, **kwargs):
        cli = MockSCPClient(transport, **kwargs)
        cli.should_timeout = True
        return cli

    service.scp_factory = timeout_scp_factory

    job = service.submit_transfer(
        device_identifier="srv-remote",
        direction="upload",
        local_path=local_file,
        remote_path="/tmp/file.txt",
        timeout=1.0,
    )
    finished = service.wait_transfer(job.id, timeout=3.0)

    assert finished.status == JobStatus.TIMEOUT
    assert finished.exit_code == 124
    assert "timed out" in finished.failure_reason


def test_scp_cancel_transfer(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]
    local_file = tmp_path / "file.txt"
    local_file.write_text("abc", encoding="utf-8")

    hang_event = threading.Event()

    def slow_scp_factory(transport, **kwargs):
        cli = MockSCPClient(transport, **kwargs)
        orig_close = cli.close

        def slow_put(*args, **kwargs):
            hang_event.wait(timeout=5.0)
            if cli.closed:
                raise paramiko.SSHException("Channel closed by user cancellation")

        def close_and_signal():
            orig_close()
            hang_event.set()

        cli.put = slow_put
        cli.close = close_and_signal
        return cli

    service.scp_factory = slow_scp_factory

    job = service.submit_transfer(
        device_identifier="srv-remote",
        direction="upload",
        local_path=local_file,
        remote_path="/tmp/file.txt",
    )

    time.sleep(0.1)
    cancelled_job = service.cancel_transfer(job.id)
    hang_event.set()

    assert cancelled_job.status == JobStatus.CANCELLED
    assert cancelled_job.exit_code == 130


def test_scp_concurrency(scp_env):
    service = scp_env["scp_service"]
    tmp_path = scp_env["tmp_path"]

    jobs = []
    for i in range(3):
        f = tmp_path / f"file_{i}.txt"
        f.write_text(f"content {i}", encoding="utf-8")
        job = service.submit_transfer(
            device_identifier="srv-remote",
            direction="upload",
            local_path=f,
            remote_path=f"/tmp/file_{i}.txt",
        )
        jobs.append(job)

    for job in jobs:
        finished = service.wait_transfer(job.id, timeout=3.0)
        assert finished.status == JobStatus.COMPLETED
        assert finished.exit_code == 0


def test_scp_orphan_recovery(scp_env):
    job_service = scp_env["job_service"]
    job_repo = scp_env["job_repo"]

    # Simula um job de transferência que ficou como RUNNING após queda abrupta
    orphan_job = Job(
        session_id="transfer-srv-remote",
        command="scp upload local='file.txt' remote='/tmp/file.txt'",
        status=JobStatus.RUNNING,
    )
    job_repo.save(orphan_job)

    recovered = job_service.recover_orphaned_jobs()
    assert recovered >= 1

    updated = job_repo.get_by_id(orphan_job.id)
    assert updated.status == JobStatus.FAILED
    assert "interrupted by service restart" in updated.failure_reason
