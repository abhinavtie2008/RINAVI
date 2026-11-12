from sqlalchemy import text

from app.core.db import engine


async def test_engine_executes_sql() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


def test_default_database_url_is_anchored_to_backend_dir() -> None:
    from app.core.config import Settings

    default = Settings.model_fields["database_url"].default
    assert "rinavi/backend/rinavi.db" in default.replace("\\", "/")
