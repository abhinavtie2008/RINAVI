# RINAVI

Independent, privacy-first AI companion for government-service applications.
Not another government portal. Your companion across all of them.

## Layout

- `apps/web` — Next.js PWA (TypeScript)
- `backend` — FastAPI modular monolith (Python)
- `infra/compose` — reference PostgreSQL/Redis/storage for staging and pilot
- `docs` — architecture decision records, compliance, evaluation
- `scripts` — bootstrap, dev, and check commands

## Quick start

```bash
scripts/bootstrap.sh   # create venv, install Python and Node dependencies
scripts/check.sh       # lint, types, and tests for backend and web
scripts/dev.sh         # run backend on :8000 and web on :3000
```

Local development uses SQLite; see `docs/architecture/decisions/0002-sqlite-dev-postgres-prod.md`.

## Planning documents

Product specification and build plan live outside this repository under `../docs/superpowers/`.
