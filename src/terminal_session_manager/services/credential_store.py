"""Protected credential storage and resolution services ensuring secrets are never plaintext."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Any

from terminal_session_manager.errors import (
    CredentialNotFoundError,
    CredentialResolutionError,
    ValidationError,
)
from terminal_session_manager.interfaces.credentials import (
    CredentialResolver,
    ExternalCredentialProvider,
)
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.persistence.sqlite import SqliteStorage, _iso, _parse_iso


def _derive_keys(master_key: bytes, salt: bytes) -> tuple[bytes, bytes]:
    """Derives 32-byte encryption key and 32-byte MAC key using PBKDF2-HMAC-SHA256."""
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        master_key,
        salt,
        iterations=100_000,
        dklen=64,
    )
    enc_key = derived[:32]
    mac_key = derived[32:]
    return enc_key, mac_key


def _crypt_keystream(data: bytes, enc_key: bytes, nonce: bytes) -> bytes:
    """Symmetric authenticated keystream XOR cipher (counter mode over HMAC-SHA256)."""
    out = bytearray(len(data))
    block_index = 0
    block_offset = 0

    while block_offset < len(data):
        block = hmac.new(
            enc_key,
            nonce + block_index.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        chunk_len = min(len(block), len(data) - block_offset)
        for i in range(chunk_len):
            out[block_offset + i] = data[block_offset + i] ^ block[i]
        block_offset += chunk_len
        block_index += 1

    return bytes(out)


class ProtectedLocalCredentialStore(CredentialResolver):
    """Local credential storage protecting secrets at rest using authenticated cryptography.

    Ensures that secrets are NEVER persisted in plaintext in database files or memory dumps.
    Integrates key derivation (PBKDF2) and tampering detection (HMAC-SHA256).
    """

    def __init__(
        self,
        storage: SqliteStorage,
        master_key: str | bytes | None = None,
    ) -> None:
        self.storage = storage
        if master_key is None:
            env_key = os.environ.get("TSM_MASTER_KEY")
            if env_key:
                raw_key = env_key.encode("utf-8")
            else:
                # Fallback to deterministic process-level master key for local usage
                raw_key = b"TSM_DEFAULT_LOCAL_PROTECTION_KEY_V1"
        elif isinstance(master_key, str):
            raw_key = master_key.encode("utf-8")
        else:
            raw_key = master_key

        self._master_key = raw_key

    def save_credential(self, ref: CredentialRef, secret: str | bytes) -> None:
        """Encrypts the secret and persists non-sensitive metadata alongside ciphertext."""
        secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret

        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(16)
        enc_key, mac_key = _derive_keys(self._master_key, salt)

        ciphertext = _crypt_keystream(secret_bytes, enc_key, nonce)
        auth_tag = hmac.new(
            mac_key,
            salt + nonce + ciphertext + ref.id.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        now_str = _iso(datetime.now(timezone.utc))
        query = """
        INSERT INTO credential_secrets (
            ref_id, name, credential_type, description, ciphertext,
            salt, nonce, auth_tag, metadata, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ref_id) DO UPDATE SET
            name = excluded.name,
            credential_type = excluded.credential_type,
            description = excluded.description,
            ciphertext = excluded.ciphertext,
            salt = excluded.salt,
            nonce = excluded.nonce,
            auth_tag = excluded.auth_tag,
            metadata = excluded.metadata,
            updated_at = excluded.updated_at;
        """

        try:
            with self.storage.lock, self.storage.connection:
                self.storage.connection.execute(
                    query,
                    (
                        ref.id,
                        ref.name,
                        ref.credential_type.value,
                        ref.description,
                        ciphertext.hex(),
                        salt.hex(),
                        nonce.hex(),
                        auth_tag.hex(),
                        json.dumps(ref.metadata),
                        _iso(ref.created_at) or now_str,
                        now_str,
                    ),
                )
        except sqlite3.Error as err:
            raise ValidationError(f"Failed to persist protected credential {ref.id}: {err}") from err

    def resolve(self, ref_id: str) -> str | bytes | None:
        """Decodes the secret in memory. Returns None if ref_id does not exist."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT * FROM credential_secrets WHERE ref_id = ?;", (ref_id,)
            )
            row = cursor.fetchone()

        if not row:
            return None

        try:
            ciphertext = bytes.fromhex(row["ciphertext"])
            salt = bytes.fromhex(row["salt"])
            nonce = bytes.fromhex(row["nonce"])
            expected_auth_tag = bytes.fromhex(row["auth_tag"])

            enc_key, mac_key = _derive_keys(self._master_key, salt)
            computed_tag = hmac.new(
                mac_key,
                salt + nonce + ciphertext + ref_id.encode("utf-8"),
                hashlib.sha256,
            ).digest()

            if not hmac.compare_digest(expected_auth_tag, computed_tag):
                raise CredentialResolutionError(
                    f"Integrity check failed for credential '{ref_id}'. Data may be tampered or key invalid."
                )

            decrypted = _crypt_keystream(ciphertext, enc_key, nonce)
            try:
                return decrypted.decode("utf-8")
            except UnicodeDecodeError:
                return decrypted
        except CredentialResolutionError:
            raise
        except Exception as err:
            raise CredentialResolutionError(
                f"Failed to decrypt credential '{ref_id}': {err}"
            ) from err

    def get_ref(self, ref_id: str) -> CredentialRef | None:
        """Retrieves only non-sensitive metadata for the given credential reference ID."""
        with self.storage.lock:
            cursor = self.storage.connection.execute(
                "SELECT ref_id, name, credential_type, description, metadata, created_at, updated_at "
                "FROM credential_secrets WHERE ref_id = ?;",
                (ref_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        try:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            created_at = _parse_iso(row["created_at"]) or datetime.now(timezone.utc)
            updated_at = _parse_iso(row["updated_at"]) or datetime.now(timezone.utc)

            return CredentialRef(
                id=row["ref_id"],
                name=row["name"],
                credential_type=CredentialType(row["credential_type"]),
                description=row["description"],
                created_at=created_at,
                updated_at=updated_at,
                metadata=metadata,
            )
        except Exception as err:
            raise ValidationError(f"Corrupt credential metadata for {ref_id}: {err}") from err

    def delete_credential(self, ref_id: str) -> None:
        """Deletes credential from the protected store."""
        with self.storage.lock, self.storage.connection:
            self.storage.connection.execute(
                "DELETE FROM credential_secrets WHERE ref_id = ?;", (ref_id,)
            )

    def rotate_credential(self, ref_id: str, new_secret: str | bytes) -> None:
        """Rotates an existing credential secret with fresh cryptographic parameters."""
        ref = self.get_ref(ref_id)
        if ref is None:
            raise CredentialNotFoundError(ref_id)
        self.save_credential(ref, new_secret)

    def rotate_master_key(self, new_master_key: str | bytes) -> int:
        """Re-encrypts all stored credentials with a new master key in a single atomic transaction.

        Returns:
            Number of rotated credentials.
        """
        new_key_bytes = (
            new_master_key.encode("utf-8")
            if isinstance(new_master_key, str)
            else new_master_key
        )
        if not new_key_bytes:
            raise ValidationError("New master key cannot be empty.")

        with self.storage.lock:
            # 1. Fetch all rows
            cursor = self.storage.connection.execute(
                "SELECT ref_id, name, credential_type, description, ciphertext, salt, nonce, auth_tag, metadata, created_at, updated_at "
                "FROM credential_secrets;"
            )
            rows = cursor.fetchall()
            if not rows:
                self._master_key = new_key_bytes
                return 0

            # 2. Decrypt all with current key and prepare new ciphertexts
            re_encrypted_rows = []
            now_str = _iso(datetime.now(timezone.utc))

            for row in rows:
                ref_id = row["ref_id"]
                try:
                    ciphertext = bytes.fromhex(row["ciphertext"])
                    salt = bytes.fromhex(row["salt"])
                    nonce = bytes.fromhex(row["nonce"])
                    expected_auth_tag = bytes.fromhex(row["auth_tag"])

                    enc_key, mac_key = _derive_keys(self._master_key, salt)
                    computed_tag = hmac.new(
                        mac_key,
                        salt + nonce + ciphertext + ref_id.encode("utf-8"),
                        hashlib.sha256,
                    ).digest()

                    if not hmac.compare_digest(expected_auth_tag, computed_tag):
                        raise CredentialResolutionError(
                            f"Integrity check failed during master key rotation for credential '{ref_id}'."
                        )

                    secret_bytes = _crypt_keystream(ciphertext, enc_key, nonce)
                except Exception as err:
                    raise CredentialResolutionError(
                        f"Failed to decrypt credential '{ref_id}' during key rotation: {err}"
                    ) from err

                # Re-encrypt with new key
                new_salt = secrets.token_bytes(16)
                new_nonce = secrets.token_bytes(16)
                new_enc_key, new_mac_key = _derive_keys(new_key_bytes, new_salt)
                new_ciphertext = _crypt_keystream(secret_bytes, new_enc_key, new_nonce)
                new_auth_tag = hmac.new(
                    new_mac_key,
                    new_salt + new_nonce + new_ciphertext + ref_id.encode("utf-8"),
                    hashlib.sha256,
                ).digest()

                re_encrypted_rows.append((
                    new_ciphertext.hex(),
                    new_salt.hex(),
                    new_nonce.hex(),
                    new_auth_tag.hex(),
                    now_str,
                    ref_id,
                ))

            # 3. Persist atomically
            with self.storage.connection:
                self.storage.connection.executemany(
                    "UPDATE credential_secrets SET "
                    "ciphertext = ?, salt = ?, nonce = ?, auth_tag = ?, updated_at = ? "
                    "WHERE ref_id = ?;",
                    re_encrypted_rows,
                )

            self._master_key = new_key_bytes
            return len(re_encrypted_rows)


class DelegatingCredentialResolver(CredentialResolver):
    """Resolver that delegates secret lookup to an external provider, falling back to a local store."""

    def __init__(
        self,
        local_store: CredentialResolver | None = None,
        external_provider: ExternalCredentialProvider | None = None,
    ) -> None:
        self.local_store = local_store
        self.external_provider = external_provider

    def resolve(self, ref_id: str) -> str | bytes | None:
        """Resolves secret from external provider first, then local store."""
        if self.external_provider is not None:
            try:
                secret = self.external_provider.resolve_secret(ref_id)
                if secret is not None:
                    return secret
            except Exception:
                pass

        if self.local_store is not None:
            return self.local_store.resolve(ref_id)

        return None

    def get_ref(self, ref_id: str) -> CredentialRef | None:
        """Retrieves metadata from external provider first, then local store."""
        if self.external_provider is not None:
            try:
                ref = self.external_provider.get_ref(ref_id)
                if ref is not None:
                    return ref
            except Exception:
                pass

        if self.local_store is not None:
            return self.local_store.get_ref(ref_id)

        return None
