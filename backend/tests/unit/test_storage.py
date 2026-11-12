import uuid
from pathlib import Path

from app.modules.vault.storage import LocalDiskStorage


def test_save_read_delete_roundtrip(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path)
    user_id = uuid.uuid4()
    document_id = uuid.uuid4()

    storage.save(user_id, document_id, b"hello vault")
    stored_path = tmp_path / str(user_id) / f"{document_id}.bin"

    assert stored_path.read_bytes() == b"hello vault"
    assert storage.read(user_id, document_id) == b"hello vault"

    storage.delete(user_id, document_id)
    assert not stored_path.exists()


def test_purge_user_removes_only_that_users_files(tmp_path: Path) -> None:
    storage = LocalDiskStorage(tmp_path)
    alice, bob = uuid.uuid4(), uuid.uuid4()
    alice_doc, bob_doc = uuid.uuid4(), uuid.uuid4()

    storage.save(alice, alice_doc, b"alice")
    storage.save(bob, bob_doc, b"bob")

    storage.purge_user(alice)

    assert not (tmp_path / str(alice)).exists()
    assert storage.read(bob, bob_doc) == b"bob"
