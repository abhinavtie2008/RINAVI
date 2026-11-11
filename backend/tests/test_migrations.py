from pathlib import Path

from alembic import command
from alembic.config import Config


def test_alembic_upgrade_head_on_clean_database(tmp_path: Path) -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", str(Path("migrations")))
    cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{tmp_path / 'migrate.db'}")

    command.upgrade(cfg, "head")

    assert (tmp_path / "migrate.db").exists()
