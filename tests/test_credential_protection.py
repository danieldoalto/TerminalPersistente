"""Tests for protected credential persistence, encryption at rest, tampering detection, and delegation."""

from pathlib import Path
import pytest

from terminal_session_manager.errors import CredentialResolutionError
from terminal_session_manager.interfaces.credentials import (
    CredentialResolver,
    ExternalCredentialProvider,
)
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.persistence.sqlite import SqliteStorage
from terminal_session_manager.services.credential_store import (
    DelegatingCredentialResolver,
    ProtectedLocalCredentialStore,
)


@pytest.fixture
def sqlite_storage(tmp_path: Path) -> SqliteStorage:
    db_file = tmp_path / "creds_test.db"
    storage = SqliteStorage(db_file)
    yield storage
    storage.close()


@pytest.fixture
def local_cred_store(sqlite_storage: SqliteStorage) -> ProtectedLocalCredentialStore:
    return ProtectedLocalCredentialStore(
        storage=sqlite_storage,
        master_key="TEST_SAFE_MASTER_KEY_ABCD1234",
    )


def test_credential_store_conforms_to_protocol(
    local_cred_store: ProtectedLocalCredentialStore,
) -> None:
    assert isinstance(local_cred_store, CredentialResolver)


def test_protected_at_rest_persistence_never_plaintext(
    local_cred_store: ProtectedLocalCredentialStore,
    sqlite_storage: SqliteStorage,
) -> None:
    ref = CredentialRef(
        name="db-prod-creds",
        credential_type=CredentialType.PASSWORD,
        description="Database admin credential",
    )
    raw_secret = "DUMMY_MOCK_SECRET_XYZ_98765"

    local_cred_store.save_credential(ref, raw_secret)

    # 1. Resolve in memory
    resolved = local_cred_store.resolve(ref.id)
    assert resolved == raw_secret

    # 2. Get non-sensitive metadata
    meta = local_cred_store.get_ref(ref.id)
    assert meta is not None
    assert meta.id == ref.id
    assert meta.name == "db-prod-creds"
    assert meta.credential_type == CredentialType.PASSWORD
    assert not hasattr(meta, "ciphertext")
    assert not hasattr(meta, "secret")

    # 3. Direct inspection on SQLite database: verify NO plaintext in the database
    with sqlite_storage.lock:
        cursor = sqlite_storage.connection.execute(
            "SELECT ciphertext, salt, nonce, auth_tag FROM credential_secrets WHERE ref_id = ?;",
            (ref.id,),
        )
        row = cursor.fetchone()

    assert row is not None
    ciphertext = row["ciphertext"]
    assert raw_secret not in ciphertext

    # Global search in credential_secrets table confirms absence of raw secret
    with sqlite_storage.lock:
        cursor = sqlite_storage.connection.execute(
            "SELECT COUNT(*) FROM credential_secrets WHERE ciphertext LIKE ? OR description LIKE ?;",
            (f"%{raw_secret}%", f"%{raw_secret}%"),
        )
        count = cursor.fetchone()[0]
    assert count == 0


def test_tampering_detection(
    local_cred_store: ProtectedLocalCredentialStore,
    sqlite_storage: SqliteStorage,
) -> None:
    ref = CredentialRef(name="api-token", credential_type=CredentialType.TOKEN)
    local_cred_store.save_credential(ref, "safe-token-value")

    # Tamper with the ciphertext directly in the database
    with sqlite_storage.lock, sqlite_storage.connection:
        sqlite_storage.connection.execute(
            "UPDATE credential_secrets SET ciphertext = 'deadbeefcafe' WHERE ref_id = ?;",
            (ref.id,),
        )

    # Attempting to resolve tampered credential must fail integrity check
    with pytest.raises(CredentialResolutionError, match="Integrity check failed"):
        local_cred_store.resolve(ref.id)


def test_wrong_master_key_fails_resolution(sqlite_storage: SqliteStorage) -> None:
    ref = CredentialRef(name="ssh-key", credential_type=CredentialType.SSH_KEY)
    store1 = ProtectedLocalCredentialStore(sqlite_storage, master_key="CORRECT_KEY_111")
    store1.save_credential(ref, "my-ssh-private-key-data")

    store2 = ProtectedLocalCredentialStore(sqlite_storage, master_key="WRONG_KEY_222")
    with pytest.raises(CredentialResolutionError):
        store2.resolve(ref.id)


def test_delegating_credential_resolver_with_external_provider(
    local_cred_store: ProtectedLocalCredentialStore,
) -> None:
    class MockExternalVaultProvider:
        """Simulates an external secret manager like Vault or AWS KMS."""

        def __init__(self) -> None:
            self._secrets = {"ext-vault-ref-01": "external-vault-secret-val"}

        def resolve_secret(self, ref_id: str) -> str | None:
            return self._secrets.get(ref_id)

        def get_ref(self, ref_id: str) -> CredentialRef | None:
            if ref_id in self._secrets:
                return CredentialRef(
                    id=ref_id,
                    name="vault-secret",
                    credential_type=CredentialType.TOKEN,
                )
            return None

    external_vault = MockExternalVaultProvider()
    assert isinstance(external_vault, ExternalCredentialProvider)

    # Local secret in sqlite
    local_ref = CredentialRef(name="local-cred", credential_type=CredentialType.PASSWORD)
    local_cred_store.save_credential(local_ref, "local-store-secret-val")

    delegating = DelegatingCredentialResolver(
        local_store=local_cred_store,
        external_provider=external_vault,
    )
    assert isinstance(delegating, CredentialResolver)

    # 1. External secret is resolved by external provider
    ext_secret = delegating.resolve("ext-vault-ref-01")
    assert ext_secret == "external-vault-secret-val"
    ext_ref = delegating.get_ref("ext-vault-ref-01")
    assert ext_ref is not None
    assert ext_ref.name == "vault-secret"

    # 2. Local secret is resolved by local store fallback
    loc_secret = delegating.resolve(local_ref.id)
    assert loc_secret == "local-store-secret-val"
    loc_ref = delegating.get_ref(local_ref.id)
    assert loc_ref is not None
    assert loc_ref.name == "local-cred"

    # 3. Non-existent returns None
    assert delegating.resolve("unknown-ref-id") is None
    assert delegating.get_ref("unknown-ref-id") is None
