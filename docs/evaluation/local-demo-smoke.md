# Local demo (Docker) — verification log

Evidence for the one-command local demo introduced in Track B PR 2
(`chore/docker-demo`, based on `main` @ `89b4be9`).

- **Date:** 2026-11-18
- **Host:** Windows 10.0.26300, Git Bash
- **Docker:** 29.9.3 (build 5457199), Compose v5.7.0
- **Base images:** `python:3.14-slim`, `node:24-slim`, `postgres:16`, `redis:7`
- **Built images:** `rinavi-backend:latest` 335 MB (`3cefb025cb09`),
  `rinavi-web:latest` 387 MB (`fad897134727`). Local images carry no repo
  digests (tag pulls on this Docker Desktop populate `RepoDigests` only for
  digest pulls), so local IDs are recorded instead.

## Compose config

`docker compose config --quiet` in `infra/compose` validates cleanly.
Services: `postgres`, `backend`, `redis`, `web`. No `minio` service, image,
or volume exists (0/0/0 by `config --services`, `docker images`, and
`docker volume ls`).

## Run 1 — fresh volume, images built from scratch

`docker compose up --build -d`:

- All four services reach **healthy** (postgres via `pg_isready`, backend
  via `/api/v1/health`, redis via `redis-cli ping`, web via `fetch`).
- `GET /api/v1/health` → `{"status":"ok"}`.
- `GET /` on the web app → 200 with CSP:

  ```
  default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'
  'unsafe-inline'; img-src 'self' data:; connect-src 'self'
  http://localhost:8000; frame-ancestors 'none'; base-uri 'self';
  form-action 'self'
  ```

  `connect-src` includes the API origin and there is no `unsafe-eval`.
- Backend runs non-root: `uid=10001(rinavi) gid=10001(rinavi)`.
- `CATALOG_ROOT` resolves to `/app/catalog/services` inside the container
  (the editable install keeps the catalog outside site-packages), and the
  directory contains `edistrict`.
- `scripts/smoke_demo.py http://127.0.0.1:8000`: **all 14 steps pass**
  (health, dev sign-in, consent, two PDF uploads, extraction without
  Aadhaar leakage, profile promotion/confirmation, draft creation, purpose,
  evidence links, declaration, export).
- Backend suite against the compose Postgres
  (`RINAVI_TEST_DATABASE_URL=postgresql+asyncpg://rinavi:rinavi@127.0.0.1:5432/rinavi_test`):
  **268 passed** in 167.78s (9 pre-existing slowapi deprecation warnings).

## Run 2 — teardown and repeat on a fresh volume

`docker compose down -v` (volumes erased), then `docker compose up -d`
using the already-built images:

- All four services healthy again.
- Smoke: **all 14 steps pass**; health returns `{"status":"ok"}`; web
  returns 200.

## Run 3 — custom ports (`WEB_PORT=3100`, `API_PORT=8001`)

`WEB_PORT=3100 API_PORT=8001 docker compose up --build -d`:

- All four services healthy.
- CORS preflight from `http://localhost:3100` and `http://127.0.0.1:3100`
  → 200 with a matching `access-control-allow-origin`; an unknown origin
  (`http://localhost:9999`) → 400.
- Web CSP `connect-src` baked as `http://localhost:8001` from `API_PORT`;
  no `unsafe-eval`.
- Backend settings render `cors_origins` and `webauthn_origin` at `:3100`.
- Smoke against `http://127.0.0.1:8001`: **all 14 steps pass**.
- Fresh-volume note: this run did not record a teardown before starting;
  the custom-port path was independently re-verified from a clean volume
  during the PR #66 review.

## Known limitations

- **Images wait for OCR.** PNG/JPEG uploads are accepted but parked as
  `needs_attention` until OCR is implemented.
- **Dev sign-in is enabled** (`RINAVI_DEV_SIGNIN_ENABLED=true`) so the
  demo works without passkeys. A hosted pilot must never set it.
- **Loopback only.** Every published port binds to `127.0.0.1`.
- **Object storage is not wired.** The vault volume is local disk;
  checklist item 64 owns object storage.
- **`rinavi_test` is created by init SQL on fresh volumes only.** On an
  existing volume, run
  `docker compose exec postgres createdb -U rinavi rinavi_test` once.
- The smoke script sets `trust_env=False`: this machine's `NO_PROXY`
  contains bare IPv6 entries (`[::1]`, `::1`) that crash httpx 0.28.1
  `Client()` init, and localhost traffic should not ride a proxy anyway.
