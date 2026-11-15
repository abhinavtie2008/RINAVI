# WP8 pilot readiness

Prepared 2026-11-15 against `main` at `ec6cb1c` (PRs #30, #31 and #33 merged,
#34 open). This is the gate the WP5 ledger sets: every deferred item must be
**cleared** or **explicitly accepted** before the controlled pilot.

Every state below was checked against the code on that commit, not copied from
the ledger. Where the ledger said "not re-verified", this pass looked.

## How to read this

- **Cleared** — the work is in `main` and a test or command in this repo covers it.
- **Accepted** — knowingly not done; the decision to ship without it has to be recorded.
- **Open** — nobody has decided yet, and the pilot should not start until somebody does.

Nothing here is a judgement about whether the pilot should proceed. That call is
the founder's; this document only makes the state visible.

## What is cleared

| Area | State | Evidence |
|---|---|---|
| Environment fails closed | An unset `RINAVI_ENVIRONMENT` is an error that names the variable; production rejects dev sign-in, insecure cookies and non-https WebAuthn origins | `core/config.py::_reject_unsafe_production`, `tests/test_config.py` |
| Rate limiting | Per-IP ceiling 1200/hour plus a per-session 200/hour budget, so one citizen cannot spend a shared connection's allowance | PR #33, `core/rate_limit.py`, `tests/integration/test_rate_limits.py` |
| Browser security headers | `nosniff`, `DENY`, `no-referrer`, `Permissions-Policy`, COOP on every response; HSTS in production | PR #25, `main.py::SECURITY_HEADERS`, `tests/security/test_security_headers.py` |
| API docs hidden in production | `/docs`, `/redoc` and `/openapi.json` are not registered when `environment=production` | PR #25, `main.py::create_app` |
| Consent, deny-by-default | Four purposes, checked as a dependency on the routes that need them; `apply-again` now also requires `applications.preparation` | PR #31, `api/deps.py`, `modules/locker/routes.py` |
| Consent withdrawal | `/consent` page lists every purpose and withdraws an active grant | PR #34 (open), `features/consent/ConsentPage.tsx` |
| Extraction accuracy | Rupee amounts keep rupees (`Rs 120,000.00` → `120000`, not 12 million); impossible dates (`31/02/2000`) stay raw at low confidence | PR #30, `documents/extraction.py`, `tests/unit/test_extraction.py` |
| Pack integrity | The loader refuses a checklist group that names a classification no document can hold | PR #30, `catalog/loader.py`, `tests/unit/test_catalog_loader.py` |
| Blob lifecycle | A record whose file is gone reports `content_unavailable` instead of 500; a rolled-back upload discards its bytes | PR #30, `documents/pipeline.py`, `vault/routes.py` |
| Audit redaction | Document contents and PII never reach the audit log; SHA-256 digests preserved | PR #17, `audit/service.py`, `tests/security/test_redaction.py` |
| Supply chain | CodeQL on push and PR, Dependabot for pip/npm/actions, branch protection, actions pinned to `@v7` | `.github/workflows/ci.yml`, PRs #20, #27–#29 |
| Test gate | `scripts/check.sh` covers ruff, pyright, pytest, eslint, `next typegen`, tsc, vitest and a production build; same gate in CI | `scripts/check.sh`; backend 218 tests, web 13 test files at this commit |

## WP5 deferred ledger — verified state

| # | Item | State | What is actually there |
|---|---|---|---|
| 1 | Async processing isolation | **Open** | `process_document` still runs inline inside the upload request (`vault/routes.py`). No worker package, no Celery/Redis dependency. A 10 MB PDF is parsed while the request is held open. |
| 2 | Encryption at rest + object storage | **Open — blocks real documents** | `LocalDiskStorage` writes plaintext bytes to `<storage_dir>/<user_id>/<document_id>.bin`. No `cryptography` dependency, no S3/MinIO client in `pyproject.toml`. `infra/compose/compose.yaml` pins `minio/minio:latest` with `rinavi`/`rinavi-dev-only` credentials, and `postgres` with `rinavi`/`rinavi` — reference only, not a hardening baseline. |
| 3 | Image OCR | **Accepted (deliberate)** | PNG/JPEG uploads come back `needs_attention` with `note = "ocr_not_configured"`, asserted in `test_document_pipeline.py`. Consequence: image evidence is unusable, so pilot instructions must say PDF or TXT. |
| 4 | Aadhaar Verhoeff validation | **Open** | `_normalize_aadhaar` accepts any 12 digits; no checksum. A mistyped Aadhaar number is stored as high-confidence. |
| 5 | Export completeness | **Open** | `GET /auth/export` returns `user` and `consent_records` only (`identity/schemas.py::AccountExport`). Document metadata and profile values are missing, so a citizen cannot take their own data with them. |
| 6 | Retention sweeps | **Open** | No scheduler or cron job exists. A document whose delete fails at `storage.delete` (503) keeps both row and file, which is recoverable by retrying; nothing sweeps files left behind by an interrupted delete. |
| 7 | PostgreSQL migration | **Open — ADR-0002 says before WP8** | `database_url` still defaults to `sqlite+aiosqlite`; local runs and CI are SQLite only. `infra/compose/compose.yaml` offers PostgreSQL 16; parity was never run against a real instance. |
| 8 | Extraction cost baseline | **Cleared by absence** | The pipeline is deterministic and makes no AI calls: no `openai`, `anthropic`, Tesseract or other inference dependency exists. Spend is zero, so there is nothing to meter yet. Correction counts already come from `profile.value_corrected` audit events. |

## Found after WP7

These are not in the WP5 ledger and are not yet on any decision log.

1. **Compliance gate is absent.** The spec's section 6 resolver — deciding whether
   a pack's requirements can be satisfied by what the citizen holds — has no
   implementation. Drafts report missing evidence per group, but nothing answers
   "can this person actually apply?". Either a minimal resolver is built or the
   pilot documents RINAVI as Assist-only, with the portal deciding eligibility.
2. **Module coverage is 9 of 11.** `backend/app/modules` contains applications,
   audit, catalog, consent, documents, identity, locker, profile and vault. The
   spec names `execution` and `integrations` as well; neither exists.
3. **There is no deployment target.** No `Dockerfile`, `Procfile`, `fly.toml` or
   render config; `infra/compose` is a reference for services, not an app stack.
   `scripts/dev.sh` is Git-Bash/Windows-only (`scripts/venv.sh` solved the venv
   half of that for bootstrap and check, not for dev).
4. **Rate-limit storage is per-process.** `rate_limit_storage_uri` defaults to
   `memory://`, so with more than one worker each process keeps its own counters
   and the effective budget multiplies. A multi-worker pilot must set a shared
   backend (`redis://`, `redis` extra already declared).
5. **Aadhaar is stored and displayed unmasked.** No masking or partial display
   exists anywhere in the app (`mask` appears in no source file). Accepted by
   decision during this hardening pass; it stays on this list because the pilot
   handles real people's numbers, not synthetic ones.
6. **One moderate dependency advisory** is reported by GitHub on the default
   branch (`https://github.com/abhinavtie2008/RINAVI/security/dependabot/1`).
   Not reviewed in this pass.
7. **Real documents remain out of scope** until the legal/privacy review and the
   security gate above are done. Everything in development and in the test suite
   is synthetic.

## Decisions needed before the gate

| # | Decision | Why it cannot be deferred |
|---|---|---|
| 1 | Real or synthetic documents in the pilot | If real: items 2, 4, 5 and 7 must clear, and item 9's masking question returns. |
| 2 | Encryption at rest + object storage | A plaintext `.bin` per citizen on local disk is the single largest exposure in the current design. |
| 3 | PostgreSQL cutover | ADR-0002 already decided it happens before WP8; SQLite in a pilot means one file, one writer. |
| 4 | Compliance gate: build the resolver, or document Assist-only | Changes what the pilot promises a citizen. |
| 5 | Export completeness | Without it, "take your data with you" is not true. |
| 6 | Aadhaar checksum + display masking | A wrong-but-accepted Aadhaar number becomes a failed application at the portal. |
| 7 | Deployment topology and worker count | Determines whether item 4 above (shared rate-limit storage) is a blocker or a note. |
| 8 | OCR scope for the pilot | If image uploads stay unsupported, say so in the pilot script rather than letting citizens discover it. |

## What this pass did not verify

- Anything in a browser: no page was driven end to end.
- PostgreSQL behaviour or Alembic parity against a real instance.
- Multi-worker or multi-instance behaviour of the rate limiter.
- Behaviour with a real document, real Aadhaar number or real portal session.
- The contents of the Dependabot advisory.
- Whether branch protection currently requires the checks it names.
