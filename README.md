# RINAVI

[![CI](https://github.com/abhinavtie2008/RINAVI/actions/workflows/ci.yml/badge.svg)](https://github.com/abhinavtie2008/RINAVI/actions/workflows/ci.yml)

Not another government portal. Your companion across all of them.

RINAVI is an independent, privacy-first companion that helps citizens prepare
and manage applications across Indian government services. The citizen stays
in control: RINAVI assists, explains, and organizes — it never submits
applications, stores portal passwords, or bypasses OTP/CAPTCHA on anyone's
behalf.

## What works today

- **Sign-in & passkeys** — dev sign-in for local work, WebAuthn passkeys, session cookies
- **Consent, deny-by-default** — every feature asks for purpose-scoped consent before touching data
- **Document vault** — upload PDF/TXT/images, stateful processing (`processed`, `needs_attention`), retry, delete
- **Extraction** — deterministic field extraction with confidence scores and `line N` locators so you can check where every value came from (OCR/LLM upgrades are planned, not assumed)
- **Profile review** — promote values from a document, review, correct, confirm — values always carry their source, and deleting the source marks them stale
- **Service catalog** — a versioned Delhi e-District income-certificate pack with official sources, guidance, evidence checklist, and form template
- **Application drafts** — confirmed profile values seed source-linked drafts; deterministic preflight leaves missing evidence unresolved, and export is a copy-ready Assist packet, never a submission
- **Application locker** — freeze a completed packet, track its journey with your own notes and reference numbers, and re-apply with your previous evidence
- **Erasure that always works** — deleting a document or your account works even after consent is withdrawn, and purges stored files
- **Redacted audit trail** — account activity is logged, but document contents and PII never reach the audit log

Data in development is synthetic only. Real documents are out of scope until
the legal/privacy review and security gate pass — that is a deliberate
policy, not a missing feature.

## Layout

- `apps/web` — Next.js PWA (TypeScript)
- `backend` — FastAPI modular monolith (Python)
- `catalog` — versioned, source-linked service definitions and form templates
- `infra/compose` — reference PostgreSQL/Redis/storage for staging and pilot
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

## Quality gate

`scripts/check.sh` runs the full gate — backend `ruff`, `pyright`, `pytest`
(111 tests) and web `eslint`, `tsc`, `vitest` (25 tests), production build.
The same gate runs in CI on every push and pull request.
