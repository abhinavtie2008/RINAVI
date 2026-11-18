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
os.environ["RINAVI_ENVIRONMENT"] = "test"
# Integration tests sign in through the dev-signin route; it is opt-in.
os.environ["RINAVI_DEV_SIGNIN_ENABLED"] = "true"
atexit.register(shutil.rmtree, _tmp, ignore_errors=True)


@pytest.fixture(autouse=True)
async def _reset_schema() -> AsyncIterator[None]:
    from app.core.db import Base, engine

    shutil.rmtree(_STORAGE_DIR, ignore_errors=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def _reset_limiter() -> None:
    from app.core.rate_limit import limiter, session_limiter

    limiter.reset()
    session_limiter.reset()
