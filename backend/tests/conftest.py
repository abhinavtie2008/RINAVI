import atexit
import os
import shutil
import tempfile
from collections.abc import AsyncIterator

import pytest

_tmp = tempfile.mkdtemp(prefix="rinavi-test-")
_STORAGE_DIR = f"{_tmp}/vault"
os.environ["RINAVI_DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp}/rinavi-test.db"
os.environ["RINAVI_STORAGE_DIR"] = _STORAGE_DIR
atexit.register(shutil.rmtree, _tmp, ignore_errors=True)


@pytest.fixture(autouse=True)
async def _reset_schema() -> AsyncIterator[None]:
    from app.core.db import Base, engine

    shutil.rmtree(_STORAGE_DIR, ignore_errors=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
