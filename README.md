# RINAVI

[![CI](https://github.com/abhinavtie2008/RINAVI/actions/workflows/ci.yml/badge.svg)](https://github.com/abhinavtie2008/RINAVI/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Not another government portal. Your companion across all of them.

**RINAVI is independent and not affiliated with, endorsed by, or acting for any government body, department, or authority.**

RINAVI is an independent, privacy-first companion that helps citizens prepare
and manage applications across Indian government services. The citizen stays
in control: RINAVI assists, explains, and organizes — it never submits
applications, stores portal passwords, or bypasses OTP/CAPTCHA on anyone's
behalf.

## What works today

- **Sign-in & passkeys** — dev sign-in for local work, WebAuthn passkeys, session cookies
- **Consent, deny-by-default** — every feature asks for purpose-scoped consent before touching data
- **Document vault** — upload PDF/TXT (images are accepted but wait for OCR), stateful processing (`processed`, `needs_attention`), retry, delete
- **Extraction** — deterministic field extraction with confidence scores and `line N` locators so you can check where every value came from (OCR/LLM upgrades are planned, not assumed)
- **Profile review** — promote values from a document, review, correct, confirm — values always carry their source, and deleting the source marks them stale
- **Service catalog** — a versioned Delhi e-District income-certificate pack with official sources, guidance, evidence checklist, and form template
- **Application drafts** — confirmed profile values seed source-linked drafts; deterministic preflight leaves missing evidence unresolved, and export is a copy-ready Assist packet, never a submission
- **Application locker** — freeze a completed packet, track its journey with your own notes and reference numbers, and re-apply with your previous evidence
- **Erasure that always works** — deleting a document or your account works even after consent is withdrawn, and purges stored files
- **Redacted audit trail** — account activity is logged, but document contents and PII never reach the audit log
- **One-command local demo** — `docker compose up` in `infra/compose` runs the full stack on PostgreSQL; a smoke script walks the whole citizen flow against it

Data in development is synthetic only. Real documents are out of scope until
the legal/privacy review and security gate pass — that is a deliberate
policy, not a missing feature.

## Layout

- `apps/web` — Next.js PWA (TypeScript)
- `backend` — FastAPI modular monolith (Python)
- `catalog` — versioned, source-linked service definitions and form templates
- `infra/compose` — one-command local demo (PostgreSQL, backend, web) with Redis provisioned for the future shared rate-limit backend (object storage is not wired yet)
- `docs` — architecture decision records, compliance, evaluation
- `scripts` — bootstrap, dev, and check commands

## Quick start

Requirements: Python 3.14, Node.js 24.

```bash
scripts/bootstrap.sh   # create venv, install Python and Node dependencies
scripts/check.sh       # lint, types, and tests for backend and web
scripts/dev.sh         # run backend on :8000 and web on :3000
```

Local development uses SQLite; see
`docs/architecture/decisions/0002-sqlite-dev-postgres-prod.md`.
`scripts/dev.sh` enables the dev sign-in route via
`RINAVI_DEV_SIGNIN_ENABLED=true`; without it (or the equivalent line in
`backend/.env`) `/api/v1/auth/dev-signin` returns 404, since dev sign-in is a
sign-in bypass and must be opted into explicitly.

## Local demo (Docker)

Requirements: Docker Desktop (or another Docker engine with Compose v2).

```bash
# from the repository root, after scripts/bootstrap.sh
cd infra/compose
docker compose up --build -d       # first build takes a few minutes
docker compose ps                  # wait until every service shows "healthy"
source ../../scripts/venv.sh && activate_backend_venv ../../backend/.venv
python ../../scripts/smoke_demo.py # walk the whole citizen flow, step by step
docker compose down -v             # stop and erase all demo data
```

The web app is at http://localhost:3000 and the API docs at
http://localhost:8000/docs. Every port binds to loopback only.

This stack is a demo, not the pilot:

- **Synthetic data only.** The smoke script generates its documents in
  memory; do not upload real citizen documents to a local demo.
- **Dev sign-in is a bypass.** The compose file sets
  `RINAVI_DEV_SIGNIN_ENABLED=true` so the demo works without passkeys;
  the hosted pilot must never set it.
- **Images wait for OCR.** PNG/JPEG uploads are accepted but parked as
  `needs_attention` until OCR is implemented.
- The `rinavi_test` database (for running the backend suite against this
  Postgres) is created automatically on a fresh volume; on an existing
  one, run
  `docker compose exec postgres createdb -U rinavi rinavi_test` once.

## Quality gate

`scripts/check.sh` runs the full gate — backend `ruff`, `pyright`, `pytest`
(268 tests) and web `eslint`, `tsc`, `vitest` (54 tests), production build.
The same gate runs in CI on every push and pull request.
