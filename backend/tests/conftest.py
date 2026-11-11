import atexit
import os
import shutil
import tempfile
from collections.abc import AsyncIterator

import pytest

_tmp = tempfile.mkdtemp(prefix="rinavi-test-")
os.environ["RINAVI_DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp}/rinavi-test.db"
atexit.register(shutil.rmtree, _tmp, ignore_errors=True)


@pytest.fixture(autouse=True)
async def _reset_schema() -> AsyncIterator[None]:
    from app.core.db import Base, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
