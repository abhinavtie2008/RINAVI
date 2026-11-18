import os

from sqlalchemy.engine import make_url


def test_engine_uses_the_test_database_url_override() -> None:
    # conftest.py must honor RINAVI_TEST_DATABASE_URL when it is set; the
    # default remains its own throwaway SQLite file. Both sides are rendered
    # through make_url so dialect-specific normalization (sqlite file paths)
    # does not create false mismatches, and the password stays visible.
    from app.core.db import engine

    override = os.environ.get("RINAVI_TEST_DATABASE_URL")
    if override:
        assert engine.url.render_as_string(hide_password=False) == make_url(
            override
        ).render_as_string(hide_password=False)
    else:
        assert str(engine.url).startswith("sqlite+aiosqlite:///")
