import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config

_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _alembic_config(db_path: Path) -> Config:
    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", str(Path("migrations")))
    cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_path}")
    return cfg


def _table_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        return {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


def test_alembic_check_reports_no_schema_drift(tmp_path: Path) -> None:
    """`alembic check` compares the metadata the migration environment loads with
    the migrated database. Because it runs in a fresh process, it fails when a
    model module is missing from `migrations/env.py` — otherwise the next
    `--autogenerate` would emit DROP TABLE for that model's table."""
    db_path = tmp_path / "check.db"
    command.upgrade(_alembic_config(db_path), "head")

    env = os.environ.copy()
    env["RINAVI_DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    env.setdefault("RINAVI_ENVIRONMENT", "test")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "check"],
        cwd=_BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "alembic detected schema drift; a model module is missing from "
        f"migrations/env.py:\n{result.stdout}\n{result.stderr}"
    )


def test_aadhaar_cleanup_migration_deletes_only_restricted_rows(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "cleanup.db"
    cfg = _alembic_config(db_path)
    command.upgrade(cfg, "a51cf575109b")

    user_id = uuid.uuid4().hex
    now = "2026-11-16 00:00:00"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO users (id, email, display_name, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, "legacy@example.com", "Legacy", now),
        )
        for field_key, value in (
            ("aadhaar_number", "123456789012"),
            ("full_name", "Asha Devi"),
        ):
            conn.execute(
                "INSERT INTO profile_values ("
                "id, user_id, field_key, value, status, correction_history, "
                "created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    uuid.uuid4().hex,
                    user_id,
                    field_key,
                    value,
                    "confirmed",
                    "[]",
                    now,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db_path)
    try:
        rows = list(
            conn.execute("SELECT field_key, value FROM profile_values ORDER BY field_key")
        )
    finally:
        conn.close()
    assert rows == [("full_name", "Asha Devi")]


def test_alembic_upgrade_head_on_clean_database(tmp_path: Path) -> None:
    db_path = tmp_path / "migrate.db"
    command.upgrade(_alembic_config(db_path), "head")

    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        tables = _table_names(db_path)
        assert {
            "alembic_version",
            "users",
            "sessions",
            "consent_records",
            "audit_events",
            "credentials",
            "documents",
            "extracted_fields",
            "profile_values",
            "application_drafts",
            "application_cases",
            "case_events",
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
        field_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(extracted_fields)")
        }
        assert {
            "id",
            "document_id",
            "field_key",
            "value",
            "confidence",
            "locator",
        } <= field_columns
        profile_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(profile_values)")
        }
        assert {
            "id",
            "user_id",
            "field_key",
            "value",
            "status",
            "source_document_id",
            "source_locator",
            "confidence",
            "stale_reason",
            "correction_history",
        } <= profile_columns
        user_columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        assert {"id", "email", "display_name", "created_at"} <= user_columns
        session_columns = {row[1] for row in conn.execute("PRAGMA table_info(sessions)")}
        assert {"id", "user_id", "token_hash", "expires_at", "revoked_at"} <= session_columns
        case_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(application_cases)")
        }
        assert {
            "id",
            "user_id",
            "draft_id",
            "service_slug",
            "service_name",
            "pack_version",
            "packet_snapshot",
            "packet_text",
            "status",
            "reference_number",
            "acknowledgement_number",
            "deadline_at",
            "outcome_notes",
            "created_at",
            "updated_at",
        } <= case_columns
        event_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(case_events)")
        }
        assert {"id", "case_id", "type", "payload", "created_at"} <= event_columns
    finally:
        conn.close()
