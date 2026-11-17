# WP8 pilot readiness

Prepared 2026-11-16 against `main` at `58b6419`, with the changes in ADR-0003
(#51) and A1 (#52) assumed merged for this gate. This is the gate the WP5
ledger sets: every deferred item must be **cleared** or **explicitly accepted**
before the controlled pilot.

Every state below was checked against the code on that commit, not copied from
the ledger. Where the ledger said "not re-verified", this pass looked.

## How to read this

- **Cleared** — the work is in `main` and a test or command in this repo covers it.
- **Accepted** — knowingly not done; the decision to ship without it is recorded below, with the condition that reopens it.
- **Recorded** — a scope or policy choice, not a missing implementation.
- **Deferred** — explicitly postponed for this synthetic-only gate.

No item is left undecided. Every accepted or deferred item names what reopens it.

## What is cleared

| Area | State | Evidence |
|---|---|---|
| Environment fails closed | An unset `RINAVI_ENVIRONMENT` is an error that names the variable; production rejects dev sign-in, insecure cookies and non-https WebAuthn origins | `core/config.py::_reject_unsafe_production`, `tests/test_config.py` |
| Rate limiting | Per-IP ceiling 1200/hour plus a per-session 200/hour budget, so one citizen cannot spend a shared connection's allowance | PR #33, `core/rate_limit.py`, `tests/integration/test_rate_limits.py` |
| Browser security headers | `nosniff`, `DENY`, `no-referrer`, `Permissions-Policy`, COOP on every response; HSTS in production | PR #25, `main.py::SECURITY_HEADERS`, `tests/security/test_security_headers.py` |
| API docs hidden in production | `/docs`, `/redoc` and `/openapi.json` are not registered when `environment=production` | PR #25, `main.py::create_app` |
| Consent, deny-by-default | Four purposes, checked as a dependency on the routes that need them; `apply-again` now also requires `applications.preparation` | PR #31, `api/deps.py`, `modules/locker/routes.py` |
| Consent withdrawal | `/consent` page lists every purpose and withdraws an active grant | PR #34, `features/consent/ConsentPage.tsx` |
| Extraction accuracy | Rupee amounts keep rupees (`Rs 120,000.00` → `120000`, not 12 million); impossible dates (`31/02/2000`) stay raw at low confidence | PR #30, `documents/extraction.py`, `tests/unit/test_extraction.py` |
| Pack integrity | The loader refuses a checklist group that names a classification no document can hold | PR #30, `catalog/loader.py`, `tests/unit/test_catalog_loader.py` |
| Blob lifecycle | A record whose file is gone reports `content_unavailable` instead of 500; a rolled-back upload discards its bytes | PR #30, `documents/pipeline.py`, `vault/routes.py` |
| Audit redaction | Document contents and PII never reach the audit log; SHA-256 digests preserved | PR #17, `audit/service.py`, `tests/security/test_redaction.py` |
| Aadhaar portal-only | Aadhaar is filtered from profile reads and promotions, draft snapshots and values, validation, export, packets, and `/vault/documents/{id}/fields`; legacy profile rows are deleted; the dead UI label is gone | PR #52, `core/privacy.py`, migration `b7e4f1a2c9d3`, `tests/unit/test_application_builder.py`, `tests/integration/test_profile_api.py` |
| Dependency advisory | `eslint` 10.15 plus a scoped `minimatch` 11 override for `typescript-estree`; `npm audit` reports 0 vulnerabilities | PR #50, `apps/web/package.json`; issue #41 closed 2026-11-16 |
| Supply chain | CodeQL on push and PR, Dependabot for pip/npm/actions, the `protect-main` ruleset requires `backend` and `web`, actions pinned to `@v7` | `.github/workflows/ci.yml`, PRs #20, #27–#29 |
| Test gate | `scripts/check.sh` covers ruff, pyright, pytest, eslint, `next typegen`, tsc, vitest and a production build; same gate in CI | `scripts/check.sh`; backend 234 tests, web 50 tests across 13 files after A1 (#52) and the cleanup batch (#54) |

## WP5 deferred ledger — verified state

| # | Item | State | What is actually there | Reopens when |
|---|---|---|---|---|
| 1 | Async processing isolation | **Accepted for the synthetic pilot** | `process_document` still runs inline inside the upload request (`vault/routes.py`). No worker package, no Celery/Redis dependency. A 10 MB PDF is parsed while the request is held open. | The pilot moves to real documents, uploads beyond the synthetic set, or overlapping users; then an async worker is required. |
| 2 | Encryption at rest + object storage | **Accepted for synthetic only** | `LocalDiskStorage` writes plaintext bytes to `<storage_dir>/<user_id>/<document_id>.bin`. No `cryptography` dependency, no S3/MinIO client in `pyproject.toml`. `infra/compose/compose.yaml` pins `minio/minio:latest` with `rinavi`/`rinavi-dev-only` credentials, and `postgres` with `rinavi`/`rinavi` — reference only, not a hardening baseline. | The first real document is accepted, or storage leaves the founder's machine. Encryption + object storage must clear before either. |
| 3 | Image OCR | **Accepted (deliberate)** | PNG/JPEG uploads come back `needs_attention` with `note = "ocr_not_configured"`, asserted in `test_document_pipeline.py`. Consequence: image evidence is unusable, so pilot instructions must say PDF or TXT. | Image evidence is needed for a pilot service; OCR then becomes in scope. |
| 4 | Aadhaar Verhoeff validation | **Moot under A1** | `_normalize_aadhaar` still accepts any 12 digits, but the value is never promoted, stored in a profile, shown in a draft, exported or put in a packet. The portal is the only place an Aadhaar number is entered or validated. | Aadhaar becomes a pack input or is stored outside `extracted_fields`; then checksum validation and a policy decision are required. |
| 5 | Export completeness | **Accepted for the synthetic pilot** | `GET /auth/export` returns `user` and `consent_records` only (`identity/schemas.py::AccountExport`). Document metadata and profile values are missing. | RINAVI promises citizens they can take their data with them, or real documents are accepted. Both require a complete export. |
| 6 | Retention sweeps | **Accepted for the synthetic pilot** | No scheduler or cron job exists. A document whose delete fails at `storage.delete` (503) keeps both row and file, which is recoverable by retrying; nothing sweeps files left behind by an interrupted delete. | Real documents are accepted or the pilot has more than one user; then a scheduled sweep and an operator runbook are required. |
| 7 | PostgreSQL migration | **Deferred — accepted ADR-0002 deviation** | `database_url` still defaults to `sqlite+aiosqlite`; local runs and CI are SQLite only. `infra/compose/compose.yaml` offers PostgreSQL 16; parity was never run against a real instance. This synthetic-only gate explicitly does not satisfy ADR-0002. | Real documents are accepted, more than one worker is used, or the pilot becomes a controlled pilot in ADR-0002's sense. PostgreSQL must clear before any of those. |
| 8 | Extraction cost baseline | **Cleared by absence** | The pipeline is deterministic and makes no AI calls: no `openai`, `anthropic`, Tesseract or other inference dependency exists. Spend is zero, so there is nothing to meter yet. Correction counts already come from `profile.value_corrected` audit events. | Any inference dependency is added. |

## Found after WP7

These are not in the WP5 ledger. They are now recorded decisions rather than
unowned gaps.

1. **Compliance gate: Assist-only.** V1 does not decide eligibility. Drafts
   report missing evidence per group, but the official portal decides whether
   the citizen can apply. [ADR-0003](../architecture/decisions/0003-v1-module-scope.md)
   records the scope. A readiness resolver is post-pilot and additive: it can
   read pack snapshots, confirmed profile values, document links and validation
   results without a schema change, and its output must stay advisory. This
   reopens if a resolver is scheduled; the portal remains authoritative.
2. **Module coverage is 9 of 11 by design.**
   `backend/app/modules` contains applications, audit, catalog, consent,
   documents, identity, locker, profile and vault. The spec names `execution`
   and `integrations` as well; ADR-0003 records both as post-pilot and neither
   is stubbed in V1. This reopens when submission automation or external portal
   integrations enter scope.
3. **There is no deployment target.** No `Dockerfile`, `Procfile`, `fly.toml` or
   render config; `infra/compose` is a reference for services, not an app stack.
   `scripts/dev.sh` is Git-Bash/Windows-only. Host selection is deferred for
   this gate, and the pilot **cannot launch** until a host is chosen and the app
   is deployed there. This reopens at launch, not at code-complete.
4. **Rate-limit storage is per-process.** `rate_limit_storage_uri` defaults to
   `memory://`, so with more than one worker each process keeps its own counters
   and the effective budget multiplies. The gate assumes a **single worker**.
   This reopens on multi-worker or autoscaling, which requires a shared backend
   (`redis://`, `redis` extra already declared).
5. **Aadhaar was stored and displayed; A1 cleared the propagation.** PR #52
   filters every API path, omits restricted bindings from new draft snapshots,
   rejects field updates for a restricted binding, and deletes legacy
   `profile_values` rows with migration `b7e4f1a2c9d3`. The extraction code
   still reads and stores Aadhaar in `extracted_fields`; the owner-only `/fields`
   response hides it, and audit logging already redacts 12-digit values. The
   checksum item is moot because the portal is the only entry point. This
   reopens if extracted fields are exposed beyond `/fields`, included in an
   export, or a pack requires Aadhaar as an input.
6. **The minimatch advisory is cleared.** PR #50 moves `eslint` to 10.15 and
   forces `@typescript-eslint/typescript-estree` onto `minimatch` 11 through a
   scoped override; the override did not break lint. `npm audit` reports 0
   vulnerabilities, and issue #41 closes when the PR lands and GitHub rescans.
   Only the older `minimatch` 3.1.5 under `eslint-config-next` remains, and it
   is outside the advisory range. This reopens if the override is removed or a
   new advisory appears.
7. **Real documents remain out of scope** until the legal/privacy review and the
   security gate above are done. Everything in development and in the test suite
   is synthetic. This reopens only when the review passes and encryption,
   retention, PostgreSQL and deployment clear together.

## Decisions recorded

| # | Decision | Recorded choice | Reopens when |
|---|---|---|---|
| 1 | Documents in the pilot | Synthetic only for this gate. | Legal/privacy review passes and the security items below clear; then real documents become possible. |
| 2 | Encryption at rest + object storage | Accept plaintext local disk for synthetic data only. | The first real document or a shared host; encryption and object storage must clear first. |
| 3 | PostgreSQL cutover | Defer PostgreSQL and explicitly accept the ADR-0002 deviation for this synthetic-only gate. | Real documents, multiple workers, or a controlled pilot; PostgreSQL must clear first. |
| 4 | Compliance resolver | Assist-only in V1; resolver is post-pilot and additive; portal decides eligibility. | A resolver is scheduled; it must stay advisory and needs a new ADR or an ADR-0003 update. |
| 5 | Export completeness | Accept user + consent records as the pilot export. | RINAVI promises "take your data with you" or accepts real documents; then document metadata and profile values must be included. |
| 6 | Aadhaar handling | Portal-only. A1 cleared profile, draft, packet and UI propagation; legacy profile rows are deleted; extraction remains but is hidden from the API; checksum is moot. | Aadhaar becomes a pack input or extracted rows are exposed beyond `/fields`. |
| 7 | Deployment topology | Defer host selection; single worker. Code-complete is not launch-ready. | Pilot launch; a host must be chosen and the app deployed before launch. |
| 8 | OCR scope | Accept PDF/TXT only; the pilot script must say image uploads are unsupported. | Image evidence is required; OCR then enters scope. |
| 9 | Concurrent workers | Accept a single worker with `memory://` rate-limit storage. | Multi-worker or autoscaling; a shared rate-limit backend is required. |
| 10 | Dependency advisory | Cleared by the eslint 10.15 + scoped `minimatch` 11 override; no fallback was needed. | The override is removed or a new advisory affects shipped code. |

## What this pass did not verify

- Anything in a browser: no page was driven end to end.
- PostgreSQL behaviour or Alembic parity against a real instance.
- Multi-worker or multi-instance behaviour of the rate limiter.
- Behaviour with a real document, real Aadhaar number or real portal session.
- The legacy-row migration against a populated production database. It is
  covered by a test that seeds rows at `a51cf575109b` and upgrades to head, and
  by a manual fresh `alembic upgrade head`; both pass.
