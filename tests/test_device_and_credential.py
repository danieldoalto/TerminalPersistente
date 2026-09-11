"""Unit tests for Device and CredentialRef models and security constraints."""

import pytest

from terminal_session_manager.errors import ValidationError
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType


def test_credential_ref_creation() -> None:
    cred = CredentialRef(
        name="bastion-key",
        credential_type=CredentialType.SSH_KEY,
        description="SSH RSA 4096 production key",
    )
    assert cred.id is not None
    assert cred.name == "bastion-key"
    assert cred.credential_type == CredentialType.SSH_KEY
    assert cred.description == "SSH RSA 4096 production key"

    # Security constraint check: CredentialRef MUST NOT have attributes containing plaintext secrets
    assert not hasattr(cred, "password")
    assert not hasattr(cred, "secret")
    assert not hasattr(cred, "private_key")


def test_credential_ref_validation() -> None:
    with pytest.raises(ValidationError, match="name"):
        CredentialRef(name="", credential_type=CredentialType.PASSWORD)

    with pytest.raises(ValidationError, match="Invalid credential type"):
        CredentialRef(name="foo", credential_type="unknown")  # type: ignore[arg-type]


def test_device_creation_and_defaults() -> None:
    device = Device(name="prod-db-01", host="192.168.1.50")
    assert device.id is not None
    assert device.name == "prod-db-01"
    assert device.host == "192.168.1.50"
    assert device.port == 22
    assert device.device_type == DeviceType.SERVER
    assert device.connection_method == ConnectionMethod.SSH
    assert device.is_active is True
    assert device.credential_ref_id is None


def test_device_with_credential_and_options() -> None:
    cred = CredentialRef(name="lab-pass", credential_type=CredentialType.PASSWORD)
    device = Device(
        name="router-core",
        host="10.0.0.1",
        port=2222,
        device_type=DeviceType.ROUTER,
        connection_method=ConnectionMethod.SSH,
        default_user="admin",
        options={"connect_timeout": 10},
        credential_ref_id=cred.id,
    )
    assert device.credential_ref_id == cred.id
    assert device.default_user == "admin"
    assert device.port == 2222
    assert device.options["connect_timeout"] == 10


def test_device_deactivation() -> None:
    device = Device(name="temp-box", host="127.0.0.1")
    assert device.is_active is True
    device.deactivate()
    assert device.is_active is False


def test_device_validation_errors() -> None:
    with pytest.raises(ValidationError, match="name"):
        Device(name="  ", host="10.0.0.1")

    with pytest.raises(ValidationError, match="host"):
        Device(name="box", host="")

    with pytest.raises(ValidationError, match="Invalid port"):
        Device(name="box", host="10.0.0.1", port=0)

    with pytest.raises(ValidationError, match="Invalid port"):
        Device(name="box", host="10.0.0.1", port=70000)

    with pytest.raises(ValidationError, match="Invalid device type"):
        Device(name="box", host="10.0.0.1", device_type="invalid")  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="Invalid connection method"):
        Device(name="box", host="10.0.0.1", connection_method="invalid")  # type: ignore[arg-type]
