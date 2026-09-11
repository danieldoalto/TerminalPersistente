"""Tests for device resolution by nickname, error handling, session injection, and output masking."""

from pathlib import Path
import sys
import time
import pytest

from terminal_session_manager.errors import (
    CredentialNotFoundError,
    DeviceInactiveError,
    DeviceNotFoundError,
)
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.models.event import EventType
from terminal_session_manager.models.session import Session
from terminal_session_manager.persistence.sqlite import (
    SqliteDeviceRepository,
    SqliteEventRepository,
    SqliteSessionRepository,
    SqliteStorage,
)
from terminal_session_manager.services.credential_store import ProtectedLocalCredentialStore
from terminal_session_manager.services.device_service import DeviceService, ResolvedConnection
from terminal_session_manager.services.local_session import LocalSession
from terminal_session_manager.transports.local_process import LocalProcessTransport


@pytest.fixture
def sqlite_storage(tmp_path: Path) -> SqliteStorage:
    db_file = tmp_path / "resolution_session.db"
    storage = SqliteStorage(db_file)
    yield storage
    storage.close()


@pytest.fixture
def device_service_and_store(
    sqlite_storage: SqliteStorage,
) -> tuple[DeviceService, ProtectedLocalCredentialStore]:
    dev_repo = SqliteDeviceRepository(sqlite_storage)
    cred_store = ProtectedLocalCredentialStore(sqlite_storage, master_key="MASTER_KEY_RES_TEST")
    dev_service = DeviceService(repository=dev_repo, credential_resolver=cred_store)
    return dev_service, cred_store


def test_resolve_connection_by_nickname(
    device_service_and_store: tuple[DeviceService, ProtectedLocalCredentialStore],
) -> None:
    dev_service, cred_store = device_service_and_store

    cred = CredentialRef(name="bastion-pw", credential_type=CredentialType.PASSWORD)
    cred_store.save_credential(cred, "SECRET_PASS_998877")

    device = dev_service.create_device(
        name="bastion-router",
        host="10.0.0.254",
        port=2222,
        device_type=DeviceType.ROUTER,
        connection_method=ConnectionMethod.SSH,
        default_user="admin",
        options={"keepalive": 30},
        credential_ref_id=cred.id,
    )

    # Resolve using nickname
    resolved = dev_service.resolve_connection("bastion-router")
    assert isinstance(resolved, ResolvedConnection)
    assert resolved.device_id == device.id
    assert resolved.device_name == "bastion-router"
    assert resolved.host == "10.0.0.254"
    assert resolved.port == 2222
    assert resolved.connection_method == ConnectionMethod.SSH
    assert resolved.default_user == "admin"
    assert resolved.options["keepalive"] == 30
    assert resolved.secret == "SECRET_PASS_998877"

    # Security check: __repr__ must hide secret
    repr_str = repr(resolved)
    assert "SECRET_PASS_998877" not in repr_str
    assert "[PROTECTED]" in repr_str


def test_resolve_connection_deactivated_or_deleted_device_fails(
    device_service_and_store: tuple[DeviceService, ProtectedLocalCredentialStore],
) -> None:
    dev_service, _ = device_service_and_store

    d1 = dev_service.create_device(name="retired-switch", host="10.0.0.50")
    dev_service.deactivate_device(d1.id)

    with pytest.raises(DeviceInactiveError, match="retired-switch"):
        dev_service.resolve_connection("retired-switch")

    d2 = dev_service.create_device(name="deleted-server", host="10.0.0.60")
    dev_service.remove_device(d2.id)

    with pytest.raises(DeviceInactiveError, match="deleted-server"):
        dev_service.resolve_connection("deleted-server")


def test_resolve_connection_device_not_found(
    device_service_and_store: tuple[DeviceService, ProtectedLocalCredentialStore],
) -> None:
    dev_service, _ = device_service_and_store

    with pytest.raises(DeviceNotFoundError, match="unknown-device"):
        dev_service.resolve_connection("unknown-device")


def test_resolve_connection_missing_credential_reference(
    device_service_and_store: tuple[DeviceService, ProtectedLocalCredentialStore],
) -> None:
    dev_service, _ = device_service_and_store

    # Device pointing to a credential reference ID that was never saved
    dev_service.create_device(
        name="orphaned-cred-device",
        host="10.0.0.70",
        credential_ref_id="non-existent-cred-id",
    )

    with pytest.raises(CredentialNotFoundError):
        dev_service.resolve_connection("orphaned-cred-device")


def test_session_device_injection_and_output_masking(
    sqlite_storage: SqliteStorage,
    device_service_and_store: tuple[DeviceService, ProtectedLocalCredentialStore],
) -> None:
    dev_service, cred_store = device_service_and_store

    secret_key = "MY_SUPER_SECRET_TOKEN_4321"
    cred = CredentialRef(name="prod-token", credential_type=CredentialType.TOKEN)
    cred_store.save_credential(cred, secret_key)

    device = dev_service.create_device(
        name="api-gateway",
        host="10.10.10.1",
        credential_ref_id=cred.id,
    )

    session_repo = SqliteSessionRepository(sqlite_storage)
    event_repo = SqliteEventRepository(sqlite_storage)

    # Subprocess simulating a terminal session that echoes back output containing the secret
    script = (
        "import sys\n"
        "line = sys.stdin.readline()\n"
        "sys.stdout.write(f'Authenticated with {line}')\n"
        "sys.stdout.flush()\n"
    )
    transport = LocalProcessTransport(command=[sys.executable, "-u", "-c", script])

    # Inject device_service and device nickname into LocalSession
    local_session = LocalSession(
        session=Session(name="gateway-session"),
        transport=transport,
        session_repo=session_repo,
        event_repo=event_repo,
        device_service=dev_service,
        device_identifier="api-gateway",
    )

    # Verify session is bound to the resolved device ID
    assert local_session.session.device_id == device.id
    persisted_session = session_repo.get_by_id(local_session.id)
    assert persisted_session is not None
    assert persisted_session.device_id == device.id

    local_session.start()

    # Write containing the secret to simulate terminal interaction
    local_session.write(f"{secret_key}\n")

    # Read output
    output = ""
    for _ in range(10):
        chunk = local_session.read_text(timeout=0.5)
        output += chunk
        if "Authenticated" in output:
            break

    time.sleep(0.2)
    local_session.close()

    # Verify event history in event_repo
    events = event_repo.get_events(local_session.id)
    stdout_events = [e for e in events if e.event_type == EventType.STDOUT]
    assert len(stdout_events) > 0

    for ev in stdout_events:
        assert secret_key not in ev.payload
        if "[REDACTED]" in ev.payload:
            assert ev.is_masked is True

    # Confirm raw SQLite database does NOT contain secret_key in events table
    with sqlite_storage.lock:
        cursor = sqlite_storage.connection.execute(
            "SELECT COUNT(*) FROM events WHERE payload LIKE ?;", (f"%{secret_key}%",)
        )
        count = cursor.fetchone()[0]
    assert count == 0
