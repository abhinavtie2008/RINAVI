import base64
import os
import shutil
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient, Cookies

from app.core.config import get_settings
from app.main import app
from app.modules.vault.storage import (
    MAGIC,
    LocalDiskStorage,
    PlaintextBlobError,
    StorageDecryptionError,
    StorageKeyMissing,
    get_storage,
)

API = "/api/v1"
SPECIMEN = "1234 5678 9012"
DOCUMENT = f"Name: Asha Devi\nAadhaar: {SPECIMEN}\n".encode()


def key() -> bytes:
    return os.urandom(32)


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode()


def path_of(root: Path, user: uuid.UUID, document: uuid.UUID) -> Path:
    return root / str(user) / f"{document}.bin"


def files_under(root: Path, pattern: str = "*") -> list[Path]:
    return sorted(item for item in root.rglob(pattern) if item.is_file())


def holds(path: Path, needle: bytes) -> bool:
    return needle in path.read_bytes()


def test_round_trip_writes_ciphertext(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    user, document = uuid.uuid4(), uuid.uuid4()

    storage.save(user, document, DOCUMENT)

    assert storage.read(user, document) == DOCUMENT
    raw = path_of(tmp_path, user, document).read_bytes()
    assert raw.startswith(MAGIC)
    assert raw != DOCUMENT
    assert SPECIMEN.encode() not in raw
    assert b"Asha Devi" not in raw


def test_no_file_under_the_root_contains_the_specimen(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    for _ in range(2):
        storage.save(uuid.uuid4(), uuid.uuid4(), DOCUMENT)

    files = files_under(tmp_path)
    assert files
    for item in files:
        assert not holds(item, SPECIMEN.encode())
        assert SPECIMEN.encode() not in str(item).encode()


def test_each_write_uses_a_fresh_nonce(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    user, document = uuid.uuid4(), uuid.uuid4()

    storage.save(user, document, DOCUMENT)
    first = path_of(tmp_path, user, document).read_bytes()
    storage.save(user, document, DOCUMENT)
    second = path_of(tmp_path, user, document).read_bytes()

    assert first != second


def test_a_modified_blob_is_rejected(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    user, document = uuid.uuid4(), uuid.uuid4()
    storage.save(user, document, DOCUMENT)
    target = path_of(tmp_path, user, document)
    tampered = bytearray(target.read_bytes())
    tampered[-1] ^= 0x01
    target.write_bytes(bytes(tampered))

    with pytest.raises(StorageDecryptionError, match="authentication"):
        storage.read(user, document)


def test_a_blob_moved_to_another_document_is_rejected(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    user, first, second = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    storage.save(user, first, DOCUMENT)
    storage.save(user, second, DOCUMENT)
    shutil.copyfile(path_of(tmp_path, user, first), path_of(tmp_path, user, second))

    with pytest.raises(StorageDecryptionError):
        storage.read(user, second)


def test_the_wrong_key_is_rejected(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    user, document = uuid.uuid4(), uuid.uuid4()
    storage.save(user, document, DOCUMENT)

    with pytest.raises(StorageDecryptionError):
        LocalDiskStorage(tmp_path, key()).read(user, document)


def test_ciphertext_without_a_key_reports_the_missing_key(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    user, document = uuid.uuid4(), uuid.uuid4()
    storage.save(user, document, DOCUMENT)

    with pytest.raises(StorageKeyMissing):
        LocalDiskStorage(tmp_path).read(user, document)


def test_plaintext_with_a_key_configured_is_refused(tmp_path: Path) -> None:
    plain = LocalDiskStorage(tmp_path)
    user, document = uuid.uuid4(), uuid.uuid4()
    plain.save(user, document, DOCUMENT)

    with pytest.raises(PlaintextBlobError):
        LocalDiskStorage(tmp_path, key()).read(user, document)


def test_a_new_instance_reads_a_blob_written_by_the_previous_one(tmp_path: Path) -> None:
    raw_key = key()
    user, document = uuid.uuid4(), uuid.uuid4()
    LocalDiskStorage(tmp_path, raw_key).save(user, document, DOCUMENT)

    assert LocalDiskStorage(tmp_path, raw_key).read(user, document) == DOCUMENT


def test_erasure_removes_the_ciphertext(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path, key())
    user, document = uuid.uuid4(), uuid.uuid4()
    storage.save(user, document, DOCUMENT)

    storage.delete(user, document)
    assert not path_of(tmp_path, user, document).exists()

    storage.save(user, document, DOCUMENT)
    storage.purge_user(user)
    assert not (tmp_path / str(user)).exists()


def test_a_key_of_the_wrong_length_is_refused_at_construction(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="32 bytes"):
        LocalDiskStorage(tmp_path, b"too-short")


def _client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=Cookies(),
    )


async def _sign_in_and_allow(client: AsyncClient) -> None:
    signed_in = await client.post(
        f"{API}/auth/dev-signin", json={"email": "citizen@example.com"}
    )
    assert signed_in.status_code == 200
    granted = await client.post(
        f"{API}/consent/grants", json={"purpose": "documents.processing"}
    )
    assert granted.status_code == 201


async def test_upload_round_trip_is_ciphertext_and_erasure_removes_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_key = key()
    monkeypatch.setenv("RINAVI_STORAGE_ENCRYPTION_KEY", b64(raw_key))
    get_settings.cache_clear()
    get_storage.cache_clear()
    root = Path(get_settings().storage_dir)
    try:
        async with _client() as client:
            await _sign_in_and_allow(client)
            created = await client.post(
                f"{API}/vault/documents",
                files={"file": ("identity.txt", DOCUMENT, "text/plain")},
            )
            assert created.status_code == 201
            document_id = uuid.UUID(created.json()["id"])

            fetched = await client.get(f"{API}/vault/documents/{document_id}/content")
            assert fetched.status_code == 200
            assert fetched.content == DOCUMENT

            stored = files_under(root, "*.bin")
            assert len(stored) == 1
            assert not holds(stored[0], SPECIMEN.encode())

            # A restart rebuilds the store from configuration; the cache clear
            # is what a fresh process would do.
            user_id = uuid.UUID(stored[0].parent.name)
            get_storage.cache_clear()
            assert get_storage().read(user_id, document_id) == DOCUMENT

            deleted = await client.delete(f"{API}/auth/account")
            assert deleted.status_code == 204
            assert files_under(root) == []
    finally:
        monkeypatch.delenv("RINAVI_STORAGE_ENCRYPTION_KEY", raising=False)
        get_settings.cache_clear()
        get_storage.cache_clear()
