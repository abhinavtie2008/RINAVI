import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="rinavi-test-")
os.environ["RINAVI_DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp}/rinavi-test.db"
