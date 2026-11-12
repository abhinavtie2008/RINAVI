from sqlalchemy import text

from app.core.db import engine


async def test_engine_executes_sql() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


def test_default_database_url_is_anchored_to_backend_dir() -> None:
    from pathlib import Path

    from app.core.config import Settings

    backend_dir = Path(__file__).resolve().parents[1].as_posix()
    default = Settings.model_fields["database_url"].default
    assert default == f"sqlite+aiosqlite:///{backend_dir}/rinavi.db"
