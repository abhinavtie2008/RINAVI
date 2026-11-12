import shutil
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class StorageBackend(Protocol):
    def save(self, user_id: uuid.UUID, document_id: uuid.UUID, data: bytes) -> None: ...

    def read(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bytes: ...

    def delete(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None: ...

    def purge_user(self, user_id: uuid.UUID) -> None: ...


class LocalDiskStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, user_id: uuid.UUID, document_id: uuid.UUID) -> Path:
        # Built only from server-generated UUIDs; client filenames never touch the path.
        return self._root / str(user_id) / f"{document_id}.bin"

    def save(self, user_id: uuid.UUID, document_id: uuid.UUID, data: bytes) -> None:
        path = self._path(user_id, document_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read(self, user_id: uuid.UUID, document_id: uuid.UUID) -> bytes:
        return self._path(user_id, document_id).read_bytes()

    def delete(self, user_id: uuid.UUID, document_id: uuid.UUID) -> None:
        self._path(user_id, document_id).unlink(missing_ok=True)

    def purge_user(self, user_id: uuid.UUID) -> None:
        shutil.rmtree(self._root / str(user_id), ignore_errors=True)


@lru_cache
def get_storage() -> LocalDiskStorage:
    return LocalDiskStorage(Path(get_settings().storage_dir))
