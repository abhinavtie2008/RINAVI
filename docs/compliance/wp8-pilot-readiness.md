# WP8 pilot readiness

Prepared 2026-11-16 against `main` at `58b6419`, with the changes in ADR-0003
(#51) and A1 (#52) assumed merged for this gate. This is the gate the WP5
ledger sets: every deferred item must be **cleared** or **explicitly accepted**
before the controlled pilot.

Every state below was checked against the code on that commit, not copied from
the ledger. Where the ledger said "not re-verified", this pass looked.

**Added 2026-11-19:** the phase A pilot paperwork is drafted in this folder and
merged in #73 (`ac8aa27`) — see "Pilot phase A artefacts" below. Its second
pass added the threat model and the portal-permission register. A review pass
corrected the data map's profile statuses, case-creation gate and audit-detail
list, the retention policy's transaction wording, the privacy notice's Aadhaar
promise and the permission register's purpose-allowlist claim. The one code
inconsistency the data map found — a draft could not be deleted after
withdrawing `applications.preparation` — is fixed by #71, with the erase
control added to the consent gate in #72. No decision recorded below changes;
the **qualified legal review** is now the only WP2 artefact still outstanding.

**Updated 2026-11-18:** Track B is closed. The six hardening PRs (#57–#62), the
PostgreSQL parity PR (#64) and the containerized demo PR (#65) are merged; the
local gate is **268 backend / 54 web** on `main` @ `d9c0474`. The demo stack
was verified from clean volumes twice (default ports) plus one custom-port
run (the custom-port path was independently re-verified from a clean volume
by the PR #66 review), the backend suite passes against the compose
PostgreSQL (268), and MinIO is dropped from the compose stack (checklist
item 92, Option A recorded).

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
| Pack integrity | The loader refuses a checklist group that names a classification no document can hold | PR #30, `backend/app/modules/catalog/loader.py`, `tests/unit/test_catalog_loader.py` |
| Blob lifecycle | A record whose file is gone reports `content_unavailable` instead of 500; a rolled-back upload discards its bytes | PR #30, `documents/pipeline.py`, `vault/routes.py` |
| Audit redaction | Document contents and PII never reach the audit log; SHA-256 digests preserved | PR #17, `audit/service.py`, `tests/security/test_redaction.py` |
| Aadhaar portal-only | Aadhaar is filtered from profile reads and promotions, draft snapshots and values, validation, export, packets, and `/vault/documents/{id}/fields`; legacy profile rows are deleted; the dead UI label is gone | PR #52, `core/privacy.py`, migration `b7e4f1a2c9d3`, `tests/unit/test_application_builder.py`, `tests/integration/test_profile_api.py` |
| Dependency advisory | `eslint` 10.15 plus a scoped `minimatch` 11 override for `typescript-estree`; `npm audit --omit=dev` reports 0 vulnerabilities; dev-only test-dependency advisories are tracked in `threat-model.md` §5.6 | PR #50, `apps/web/package.json`; issue #41 closed 2026-11-16 |
| Supply chain | CodeQL on push and PR, Dependabot for pip/npm/actions, the `protect-main` ruleset requires `backend`, `web`, `backend-postgres` and `docker`, actions pinned to major tags | `.github/workflows/ci.yml`, PRs #20, #27–#29 |
| Security hardening | Prefix-negative income forms stay raw; request strings are capped; the retry route shares the upload budget; dev sign-in is opt-in; traceback redaction covers `exc_info`, `stack_info` and uvicorn's own handlers; request bodies are capped (1 MB JSON / 11 MB otherwise); PDF parsing is bounded (100 pages / 2 MB text) and runs off the event loop; the web app sends a static CSP | PRs #57–#62; `tests/security/test_redaction.py`, `tests/integration/test_body_limits.py`, `tests/integration/test_document_pipeline.py`, `apps/web/src/lib/csp.test.ts` |
| Test gate | CI is the gate, on every push and PR: backend (pip-audit, ruff, pyright, pytest on SQLite), `backend-postgres` (migrations, `alembic check`, then the suite against PostgreSQL), web (demo drift, `npm audit --omit=dev`, eslint, `next typegen`, tsc, vitest, production build), `docker` (both images, the UID and entrypoint contract, compose validation), and `e2e` on PRs that can touch the journeys. `scripts/check.sh` is the local subset and its gap against CI is #141. Counts are not repeated here: they change with every PR and CI prints them. | `.github/workflows/ci.yml`, `scripts/check.sh` |
| Local containerized demo | One command starts the whole app on PostgreSQL: `docker compose up` in `infra/compose` builds non-root backend (UID 10001) and web images, applies migrations, and passes a 14-step smoke of the citizen flow; every port binds to loopback; no MinIO | PR #65, `scripts/smoke_demo.py`, `docs/evaluation/local-demo-smoke.md`; two clean-volume runs (default ports) plus one custom-port run, backend suite green against the compose PostgreSQL |

## WP5 deferred ledger — verified state

| # | Item | State | What is actually there | Reopens when |
|---|---|---|---|---|
| 1 | Async processing isolation | **Accepted for the synthetic pilot** | `process_document` still runs inline inside the upload request (`vault/routes.py`). No worker package, no Celery/Redis dependency. A 10 MB PDF is parsed while the request is held open. | The pilot moves to real documents, uploads beyond the synthetic set, or overlapping users; then an async worker is required. |
| 2 | Encryption at rest + object storage | **Blob encryption landed (item 101, `f541019`); object storage deferred** (D2, 2026-11-24) | `LocalDiskStorage` writes `MAGIC ‖ nonce ‖ AES-GCM` ciphertext for each blob, with the user and document ids as associated data; plaintext is read only while no key is configured, which production refuses (`Settings.storage_key`). `cryptography>=43` is now declared. No S3/MinIO client: MinIO was dropped when it died upstream (checklist item 92, Option A), and item 64 still owns object storage. | Object storage is scheduled, or a real document is accepted — which additionally needs the key carried by the backup gate (G7) and the runbook wipe (§5). |
| 3 | Image OCR | **Accepted (deliberate)** | PNG/JPEG uploads come back `needs_attention` with `note = "ocr_not_configured"`, asserted in `test_document_pipeline.py`. Consequence: image evidence is unusable, so pilot instructions must say PDF or TXT. | Image evidence is needed for a pilot service; OCR then becomes in scope. |
| 4 | Aadhaar Verhoeff validation | **Moot under A1** | `_normalize_aadhaar` still accepts any 12 digits, but the value is never promoted, stored in a profile, shown in a draft, exported or put in a packet. The portal is the only place an Aadhaar number is entered or validated. | Aadhaar becomes a pack input or is stored outside `extracted_fields`; then checksum validation and a policy decision are required. |
| 5 | Export completeness | **Accepted for the synthetic pilot** (D7, 2026-11-24 — no portability promise; the narrow export is reachable at `/account`, item 102) | `GET /auth/export` returns `user` and `consent_records` only (`identity/schemas.py::AccountExport`). Document metadata and profile values are missing. | RINAVI promises citizens they can take their data with them, or real documents are accepted. Both require a complete export. |
| 6 | Retention sweeps | **Accepted for the synthetic pilot** | No scheduler or cron job exists. A document whose delete fails at `storage.delete` (503) keeps both row and file, which is recoverable by retrying; nothing sweeps files left behind by an interrupted delete. | Real documents are accepted or the pilot has more than one user; then a scheduled sweep and an operator runbook are required. |
| 7 | PostgreSQL migration | **Parity cleared; production cutover still deferred** | `asyncpg` is declared (PR #64), a `backend-postgres` CI job runs the full suite against PostgreSQL 16 (268 passed), Alembic `upgrade head` and `alembic check` pass against Postgres, and the compose demo stack runs the backend on PostgreSQL. `database_url` still defaults to `sqlite+aiosqlite` for local dev/test. | Real documents are accepted or the pilot host is chosen; the production cutover (checklist items 53/67) must still land before either. |
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
3. **The app images exist; the host does not.** PR #65 added backend and web
   Dockerfiles (non-root, migrations-before-uvicorn, Next standalone) and
   turned `infra/compose` into a working app stack with a 14-step smoke of the
   citizen flow. No host has been chosen, `scripts/dev.sh` is
   Git-Bash/Windows-only, and the pilot **cannot launch** until a host is
   chosen and the app is deployed there. This reopens at launch, not at
   code-complete.
4. **Rate-limit storage is per-process.** `rate_limit_storage_uri` defaults to
   `memory://`, so with more than one worker each process keeps its own counters
   and the effective budget multiplies. The gate assumes a **single worker**.
   This reopens on multi-worker or autoscaling, which requires a shared backend
   (`redis://`, `redis` extra already declared).
5. **Aadhaar was stored and displayed; A1 cleared the propagation.** PR #52
   filters every API path, omits restricted bindings from new draft snapshots,
   rejects field updates for a restricted binding, and deletes legacy
   `profile_values` rows with migration `b7e4f1a2c9d3`. The extraction code
   still recognises an Aadhaar line so the document classifies, but
   `documents/pipeline.py` now stores the literal marker `[REDACTED]` instead
   of the digits; the owner-only `/fields` response hides the row, and audit
   logging already redacts 12-digit values. The checksum item is moot because
   the portal is the only entry point. This reopens if extracted fields are
   exposed beyond `/fields`, included in an export, or a pack requires Aadhaar
   as an input.
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
| 2 | Encryption at rest + object storage | Blob-level encryption is in place for the synthetic pilot (item 101, `f541019`); the database stays plaintext and object storage stays deferred. | Object storage is scheduled, a shared host is used, or the key must live off the host. |
| 3 | PostgreSQL cutover | Parity cleared (PR #64: `asyncpg`, `backend-postgres` CI job, 268 passed against PostgreSQL 16, Alembic verified); the production cutover itself stays deferred per ADR-0002. | Real documents or a chosen pilot host; the cutover must land before either. |
| 4 | Compliance resolver | Assist-only in V1; resolver is post-pilot and additive; portal decides eligibility. | A resolver is scheduled; it must stay advisory and needs a new ADR or an ADR-0003 update. |
| 5 | Export completeness | Accept user + consent records as the pilot export (D7, 2026-11-24: no portability promise is made). The control is reachable from the account screen before the pilot — item 102, measured by `pilot-plan.md` §7. | RINAVI promises "take your data with you" or accepts real documents; then document metadata and profile values must be included. |
| 6 | Aadhaar handling | Portal-only. A1 cleared profile, draft, packet and UI propagation; legacy profile rows are deleted; extraction still recognises the line but stores `[REDACTED]`, never the digits; checksum is moot. | Aadhaar becomes a pack input, extracted rows carry the number again, or they are exposed beyond `/fields`. |
| 7 | Deployment topology | App images and a working compose demo stack exist (PR #65); host selection stays deferred; single worker with `memory://` rate limits. | Pilot launch; a host must be chosen and the app deployed before launch. |
| 8 | OCR scope | Accept PDF/TXT only; the pilot script must say image uploads are unsupported. | Image evidence is required; OCR then enters scope. |
| 9 | Concurrent workers | Accept a single worker with `memory://` rate-limit storage. | Multi-worker or autoscaling; a shared rate-limit backend is required. |
| 10 | Dependency advisory | Cleared by the eslint 10.15 + scoped `minimatch` 11 override; no fallback was needed. | The override is removed or a new advisory affects shipped code. |

**Dependency lock — drafted, not in effect.** `backend/requirements.lock`
(draft PR #94) pins every runtime and dev requirement with hashes for Python
3.12+, resolved from `backend/pyproject.toml` with `uv pip compile
pyproject.toml --extra dev --python-version 3.12 --universal --generate-hashes`.
Nothing installs from it and no job refreshes it, so it is parked deliberately:
landing an unread pin set would look authoritative while drifting. D4 chose
option (b) — CI and the images install with `pip install --require-hashes -r
requirements.lock`, and a weekly job regenerates the lock and fails on drift;
the draft is closed as superseded once that wiring lands. Until then
`pyproject.toml` is the only install source.

## Pilot phase A artefacts

**Added 2026-11-19.** The WP2 paperwork for the synthetic pilot is drafted in
this folder. It was written against the code on `main` @ `fee4e9f` — table and
column names, the four purposes, the deletion paths and the retention gaps were
read out of the repository, not assumed. It is **draft pending the qualified
review** and changes no decision recorded above: item 83's gate is still
conditional on that review, so real documents and any hosted pilot stay blocked.

| File | What it settles | State |
|---|---|---|
| `pilot-plan.md` | How phase A runs: cohort, session format, success measures, stop conditions, reopen trigger for a real pilot | Draft |
| `data-map.md` | Every store, the personal data in it, which purpose gates it, who can see it, and the gaps the mapping exposes | Draft |
| `privacy-notice-draft.md` | Citizen-facing notice in plain English, including the export limitation, the encrypted-blob / plaintext-database split and the no-backup limitation | Draft |
| `terms-draft.md` | Pilot participation terms: prototype, synthetic documents only, no government affiliation, liability, jurisdiction | Draft |
| `retention-policy.md` | Per-store retention, deletion mechanics, what survives an account deletion and why, close-out steps | Draft |
| `recording-consent.md` | Separate consent for notes and recordings, the retention period and the facilitator script | Draft |
| `portal-permission-register.md` | Which portals exist in scope, the access level allowed to each (all A0 today), the prohibitions that are structural rather than promises, the citizen-authorisation model and the six open items for the reviewer | Draft, not signed off |
| `threat-model.md` | Assets, actors, trust boundaries, 31 threats with the control that covers each, and eight risks accepted for synthetic data with their reopen triggers | Draft |
| `reviewer-brief.md` | One page for the qualified reviewer: what is in scope, the three open consent and erasure questions, and the eight accepted risks with their reopen triggers | Draft, for the reviewer |

What the mapping surfaced, for the reviewer rather than for a code change:

1. **Aadhaar is recognised but no longer written.** `documents/pipeline.py`
   stores `[REDACTED]` for the `aadhaar_number` field instead of the digits, so
   a database reader sees that the line existed but not its value. The field
   key still classifies the document as identity. Reopens if a pack needs the
   number or a reader starts depending on the stored value.
2. **Two consent-scope questions.** `POST /applications/drafts/{id}/complete`
   snapshots draft values and evidence under `applications.preparation` alone;
   `apply-again` requires both `locker.tracking` and `applications.preparation`.
   Promotion reads document fields but is gated on `profile.storage`. Both are
   recorded in `data-map.md` §4 as questions to confirm, not as findings.
3. **Deletion is hard and immediate, but nothing expires by itself.** Expired
   sessions, old audit rows and orphaned blobs have no sweep (item 68). Cases
   and confirmed profile values have no delete route — only account deletion
   removes them; non-confirmed values can be rejected. `retention-policy.md` §5
   lists each gap with its owner. The one deletion inconsistency the map found —
   draft deletion gated while document deletion was not — is fixed in PR #71, so
   erasure no longer depends on a withdrawn grant.

The WP2 artefact set is now drafted: the **portal-permission register** and the
**threat model** were added on 2026-11-19, leaving the **qualified legal
review** as the only thing still missing — which no repository change can
provide. Item 83 stays unticked until that review signs off; the gate remains
**conditional**: real documents and any hosted pilot are blocked until then.

## Track B follow-ups (recorded, not blocking)

Raised by the PR #65 review; each is recorded with what reopens it, or who
owns it where no reopen condition applies.

1. **Docker CI job — cleared 2026-11-18.** `ci.yml` gained a path-filtered
   `docker` job (PR #68, `fee4e9f`) that builds both images with Buildx,
   validates the compose file, and asserts the image contract (UID 10001, an
   entrypoint that runs `alembic upgrade head`); it is not the full smoke, which
   stays a local pre-demo step. Reopens if the job is removed, or stops running
   on PRs that touch `backend/`, `apps/web/`, `infra/compose/` or `ci.yml`.
2. **The backend image is compose-only.** `docker run rinavi-backend` fails at
   startup (`RINAVI_ENVIRONMENT` is required) and its default SQLite/storage
   paths are root-owned. The image exists for the compose demo; standalone use
   is unsupported until someone needs it.
3. **Smoke is API-only.** `scripts/smoke_demo.py` drives the backend API; the
   web shell (CSP, CORS, baked API URL) was checked over HTTP and by the PR
   #65 review's browser pass. The CORS allow-list includes
   `http://127.0.0.1:<port>`, but the baked API URL is `localhost` and the
   session cookie is `SameSite=Lax`, so a page loaded from `127.0.0.1`
   would not send the cookie — the loopback-origin allowance covers the API
   client, not full UI auth from the alternate hostname. WP11 (checklist
   item 85) still owns browser/E2E journeys. Reopens when the web shell
   changes materially or the demo becomes part of the launch path.
4. **Floating base-image tags.** `python:3.14-slim`, `node:24-slim`,
   `postgres:16`, `redis:7` track their channels; digest pinning was declined
   for now so patch updates keep flowing. Reopens if reproducible builds
   matter more than automatic patches.
5. **Stale `compose_postgres_data` volume.** The pre-demo compose project left
   a volume that the `rinavi` project's `down -v` does not remove; delete it
   manually (`docker volume rm compose_postgres_data`) once its data is
   unwanted. Reopens if the old compose project is ever restarted or the
   volume reappears on this machine.
6. **PDF parsing has a soft, not hard, wall-clock bound.**
   `extract_text_from_pdf` checks a 20-second deadline between pages and
   returns the text read so far, so a single hostile page can still outlast
   it. Uploads run inside the request on one worker
   (threat-model.md §6.8). A hard bound needs a separate process or a job queue
   that can be killed; until then the page and text limits bound the work and
   the pilot is supervised. Reopens with concurrent users, a real document set
   or a job queue.
7. **No reverse proxy, so no proxy-level timeouts.** The compose stack exposes
   the backend and web servers directly; the only client-side bounds are the
   web app's 30-second request and 120-second upload timeouts
   (`apps/web/src/lib/api.ts`). A host with a proxy must set read/send
   timeouts at least as long as those, and the threat model must be redone
   (review trigger 1). Reopens at host selection.
8. **GitHub Pages publishes the whole `docs/` tree, not just the demo.**
   `docs/index.html` and `docs/assets/` are the static demo, but the same site
   also serves this readiness document, the pilot plan, the handbook and the
   dated planning snapshot. They contain no pilot data, but they are public and
   some are dated; treat publication of anything under `docs/` as publication
   to the internet (`data-map.md` §10).

## What this pass did not verify

- The compose demo stack in a browser: on this machine the web shell, CSP
  and CORS were checked over HTTP only; the PR #65 review's browser pass
  (dev sign-in, consent, profile flows) ran against its own compose stack,
  not the stack used in this pass.
- Multi-worker or multi-instance behaviour of the rate limiter.
- Behaviour with a real document, real Aadhaar number or real portal session.
- The legacy-row migration against a populated production database. It is
  covered by a test that seeds rows at `a51cf575109b` and upgrades to head, and
  by a manual fresh `alembic upgrade head`; both pass.
