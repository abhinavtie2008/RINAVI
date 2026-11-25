"""Encrypted-at-rest storage for uploaded document blobs (item 101, D2).

The blob is the only place a citizen's document text exists on disk, so the
written form is authenticated ciphertext: AES-GCM, a fresh nonce per write, and
the user/document pair bound as associated data, so a blob cannot be moved
between documents or accounts and still read. Plaintext is only accepted while
no key is configured, which Settings limits to development and test.
"""

import os
import shutil
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

# Versioned magic prefix. A blob without it predates item 101 and is read as
# plaintext only when no key is configured; the prefix never appears in a
# document, so detection cannot be confused by uploaded content.
MAGIC = b"RINAVI-BLOB-1\x00"
NONCE_BYTES = 12
KEY_BYTES = 32


class StorageEncryptionError(RuntimeError):
    """A stored blob cannot be read back under the current configuration."""


class StorageKeyMissing(StorageEncryptionError):
    """The blob is ciphertext but no key is configured."""


class StorageDecryptionError(StorageEncryptionError):
    """Wrong key, modified ciphertext, or a blob moved to another document."""


class PlaintextBlobError(StorageEncryptionError):
    """A plaintext blob was found while encryption is configured."""


class StorageBackend(Protocol):
    def save(self, user_id: uuid.UUID, document_id: uuid.UUID, data: bytes) -> None: ...

    def read(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bytes: ...

    def delete(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None: ...

    def purge_user(self, user_id: uuid.UUID) -> None: ...


class LocalDiskStorage:
    def __init__(self, root: Path, key: bytes | None = None) -> None:
        if key is not None and len(key) != KEY_BYTES:
            raise ValueError(f"storage key must be {KEY_BYTES} bytes")
        self._root = root
        self._key = key

    def _path(self, user_id: uuid.UUID, document_id: uuid.UUID) -> Path:
        # Built only from server-generated UUIDs; client filenames never touch the path.
        return self._root / str(user_id) / f"{document_id}.bin"

    def _aad(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bytes:
        # Binding the path means a file copied to another document or user
        # fails authentication instead of decrypting into the wrong record.
        return f"{user_id}/{document_id}".encode("ascii")

    def save(self, user_id: uuid.UUID, document_id: uuid.UUID, data: bytes) -> None:
        path = self._path(user_id, document_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._key is None:
            path.write_bytes(data)
            return
        nonce = os.urandom(NONCE_BYTES)
        sealed = AESGCM(self._key).encrypt(nonce, data, self._aad(user_id, document_id))
        path.write_bytes(MAGIC + nonce + sealed)

    def read(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bytes:
        raw = self._path(user_id, document_id).read_bytes()
        if not raw.startswith(MAGIC):
            if self._key is not None:
                raise PlaintextBlobError(
                    "document blob is stored in plaintext while storage encryption is "
                    "configured; re-upload the document or unset the key"
                )
            return raw
        if self._key is None:
            raise StorageKeyMissing(
                "document blob is encrypted but no storage key is configured"
            )
        nonce = raw[len(MAGIC) : len(MAGIC) + NONCE_BYTES]
        sealed = raw[len(MAGIC) + NONCE_BYTES :]
        if len(nonce) != NONCE_BYTES or not sealed:
            raise StorageDecryptionError("encrypted document blob is truncated")
        try:
            return AESGCM(self._key).decrypt(nonce, sealed, self._aad(user_id, document_id))
        except InvalidTag as exc:
            raise StorageDecryptionError(
                "document blob failed authentication: wrong key, modified file, or a "
                "blob moved to another document"
            ) from exc

    def delete(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        self._path(user_id, document_id).unlink(missing_ok=True)

    def purge_user(self, user_id: uuid.UUID) -> None:
        path = self._root / str(user_id)
        if not path.exists():
            return
        shutil.rmtree(path)


@lru_cache
def get_storage() -> LocalDiskStorage:
    settings = get_settings()
    return LocalDiskStorage(Path(settings.storage_dir), settings.storage_key())
