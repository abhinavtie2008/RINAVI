import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_alembic_upgrade_head_on_clean_database(tmp_path: Path) -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", str(Path("migrations")))
    cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{tmp_path / 'migrate.db'}")

    command.upgrade(cfg, "head")

    db_path = tmp_path / "migrate.db"
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {
            "alembic_version",
            "users",
            "sessions",
            "consent_records",
            "audit_events",
            "credentials",
            "documents",
        } <= tables
        document_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(documents)")
        }
        assert {
            "id",
            "user_id",
            "original_filename",
            "content_type",
            "size_bytes",
            "status",
            "classification",
            "note",
        } <= document_columns
        user_columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        assert {"id", "email", "display_name", "created_at"} <= user_columns
        session_columns = {row[1] for row in conn.execute("PRAGMA table_info(sessions)")}
        assert {"id", "user_id", "token_hash", "expires_at", "revoked_at"} <= session_columns
    finally:
        conn.close()
