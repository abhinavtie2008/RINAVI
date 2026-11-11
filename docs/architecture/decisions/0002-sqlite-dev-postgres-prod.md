# ADR-0002: SQLite for local development, PostgreSQL for staging and pilot

**Status:** Accepted (2026-11-11, founder decision)

## Decision

Local development and tests run on SQLite through SQLAlchemy async and
Alembic. PostgreSQL 16 remains the staging, pilot, and production database;
`infra/compose/compose.yaml` documents the reference services.

## Rationale

The buildathon machine has no Docker, PostgreSQL, or Redis installed.
SQLite starts instantly and keeps the migration pipeline (Alembic) the same
as production. The sprint deadline makes tool installation a poor trade.

## Consequences

- All schema changes go through Alembic migrations; no raw SQLite-only DDL
  in application code.
- Avoid SQLite-specific SQL features in queries; keep them portable.
- Enable SQLite foreign-key enforcement in tests if referential integrity
  is asserted.
- pgvector is added only when curated service retrieval is built, after the
  first workflow milestone.
- Switch to PostgreSQL before the controlled pilot (WP8).
