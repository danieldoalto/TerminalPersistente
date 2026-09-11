"""Tests for DeviceRepository and DeviceService CRUD, state transitions, and querying."""

from pathlib import Path
import pytest

from terminal_session_manager.errors import (
    DeviceInactiveError,
    DeviceNotFoundError,
    ValidationError,
)
from terminal_session_manager.interfaces.device import DeviceRepository
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.persistence.sqlite import SqliteDeviceRepository, SqliteStorage
from terminal_session_manager.services.device_service import DeviceService


@pytest.fixture
def sqlite_storage(tmp_path: Path) -> SqliteStorage:
    db_file = tmp_path / "devices_test.db"
    storage = SqliteStorage(db_file)
    yield storage
    storage.close()


@pytest.fixture
def device_repo(sqlite_storage: SqliteStorage) -> SqliteDeviceRepository:
    return SqliteDeviceRepository(sqlite_storage)


@pytest.fixture
def device_service(device_repo: SqliteDeviceRepository) -> DeviceService:
    return DeviceService(device_repo)


def test_sqlite_device_repository_conforms_to_protocol(device_repo: SqliteDeviceRepository) -> None:
    assert isinstance(device_repo, DeviceRepository)


def test_device_crud_lifecycle(device_service: DeviceService) -> None:
    # 1. Create / Register
    device = device_service.create_device(
        name="web-prod-01",
        host="192.168.10.101",
        port=2222,
        device_type=DeviceType.SERVER,
        connection_method=ConnectionMethod.SSH,
        default_user="deploy",
        options={"timeout": 15},
    )
    assert device.id is not None
    assert device.name == "web-prod-01"
    assert device.host == "192.168.10.101"
    assert device.port == 2222
    assert device.is_active is True
    assert device.is_deleted is False

    # 2. Get by ID and by Name
    by_id = device_service.get_device(device.id)
    assert by_id is not None
    assert by_id.name == "web-prod-01"

    by_name = device_service.get_device_by_name("web-prod-01")
    assert by_name is not None
    assert by_name.id == device.id

    # 3. Update
    updated = device_service.update_device(
        device.id,
        host="192.168.10.102",
        port=22,
        options={"timeout": 30, "proxy": "jump.internal"},
    )
    assert updated.host == "192.168.10.102"
    assert updated.port == 22
    assert updated.options["proxy"] == "jump.internal"

    # Verify persistence of update
    reloaded = device_service.get_device(device.id)
    assert reloaded is not None
    assert reloaded.host == "192.168.10.102"
    assert reloaded.port == 22

    # 4. List active
    active = device_service.list_devices(only_active=True)
    assert len(active) == 1
    assert active[0].id == device.id


def test_device_deactivation_and_logical_removal(device_service: DeviceService) -> None:
    d1 = device_service.create_device(name="edge-router", host="10.0.0.1", device_type=DeviceType.ROUTER)
    d2 = device_service.create_device(name="core-switch", host="10.0.0.2", device_type=DeviceType.SWITCH)

    assert len(device_service.list_devices(only_active=True)) == 2

    # Deactivate d1
    device_service.deactivate_device(d1.id)
    d1_fetched = device_service.get_device(d1.id)
    assert d1_fetched is not None
    assert d1_fetched.is_active is False
    assert d1_fetched.is_deleted is False

    # List active only returns d2
    active = device_service.list_devices(only_active=True)
    assert len(active) == 1
    assert active[0].id == d2.id

    # List non-deleted returns both
    all_non_deleted = device_service.list_devices(only_active=False)
    assert len(all_non_deleted) == 2

    # Remove d2 logically
    device_service.remove_device(d2.id)
    d2_fetched = device_service.get_device(d2.id)
    assert d2_fetched is not None
    assert d2_fetched.is_deleted is True
    assert d2_fetched.is_active is False

    # Now active is empty
    assert len(device_service.list_devices(only_active=True)) == 0
    # Non-deleted only contains d1
    assert len(device_service.list_devices(only_active=False)) == 1
    assert device_service.list_devices(only_active=False)[0].id == d1.id


def test_duplicate_device_name_rejected(device_service: DeviceService) -> None:
    device_service.create_device(name="firewall-main", host="10.1.1.1")

    with pytest.raises(ValidationError, match="conflict|already exists"):
        device_service.create_device(name="firewall-main", host="10.1.1.2")


def test_device_not_found_errors(device_service: DeviceService) -> None:
    with pytest.raises(DeviceNotFoundError):
        device_service.update_device("non-existent-id", host="1.1.1.1")

    with pytest.raises(DeviceNotFoundError):
        device_service.deactivate_device("non-existent-id")

    with pytest.raises(DeviceNotFoundError):
        device_service.remove_device("non-existent-id")
