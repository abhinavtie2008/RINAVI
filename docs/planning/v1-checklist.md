# RINAVI — V1 Final Build & Launch Plan

> **Snapshot:** 2026-11-18, from the working checklist at `main` @ `d9c0474` (268 backend / 54 web). The working copy lives outside this repository and is maintained by Qoder; refresh this file at milestones. `docs/compliance/wp8-pilot-readiness.md` remains authoritative for compliance decisions, and ADR-0003 for module scope.

**Prepared:** 2026-11-16, against `main` @ `58b6419` (backend gate 218, web gate 50).
**Updated:** 2026-11-18, `main` @ `d9c0474` (backend gate 268, web gate 54, CI green). **All six security-hardening PRs merged**: #57 `4525f8c` (item 91), #58 `4eb46b4` (items 93, 94, 96), #59 `8f7f21f` (item 95), #60 `5315df9` (item 97), #61 `f2f8a9d` (item 98), #62 `df27f11` (item 99) — **code-complete V1 plus the hardening batch is reached**. **Track B closed 2026-11-18**: PR #64 (`89b4be9`, PostgreSQL parity: `asyncpg` + `backend-postgres` CI job, 268 passed against PostgreSQL 16, Alembic verified) and PR #65 (`d9c0474`, containerized demo: backend/web Dockerfiles, full compose stack, 14-step smoke, custom-port fix squashed into `d9c0474`). The cleanup train (#54 `059f678`, #55 `f7ab071`, #56 `9ec25cc`) remains in history.
**Sources:** `docs/compliance/wp8-pilot-readiness.md`, ADR-0001/0002/0003, `docs/superpowers/plans/2026-11-09-rinavi-structured-build.md` (the WP1–WP12 roadmap), and a fresh deep scan of the repo.
**Scope:** this is the final plan for the **code-complete V1 build** — the nine modules of ADR-0003 delivering one reliable e-District income-certificate workflow, Assist-only. The master plan is the wider WP1–WP12 launch roadmap; Part 11 tracks the parts of it that sit outside this build. `docs/compliance/wp8-pilot-readiness.md` stays authoritative for compliance decisions, and ADR-0003 for module scope. Accepted V1 deviations from the master plan: no OCR, no async workers, no encryption at rest, no PostgreSQL/pgvector cutover, no browser extension, no `execution`/`integrations`, and no compliance resolver.
**How to use:** this is a dated snapshot. The checkboxes and statuses describe the state above, not a live tracker; make changes in the working copy and refresh this file at milestones.
**Checklist keeper:** Qoder maintains the working copy outside the repo; this file is refreshed at milestones.

Status legend:

- **DONE** — merged in `main` and covered by tests/CI.
- **IN PROGRESS** — a PR or branch exists right now.
- **PENDING** — planned for V1, not started.
- **DECIDED** — decision recorded, work or acceptance still to land.
- **PARTIAL** — one part landed in `main`; the rest stays deferred to a named step. Checked `[x]` because the landed part is settled.
- **PARITY CLEARED** — proven against PostgreSQL (CI job plus Alembic); the production cutover itself is still deferred.
- **DEFERRED** — explicitly out of V1; the trigger states what reopens it.
- **OPEN** — nobody has decided yet.

**Checkbox:** `[x]` = settled — DONE, DECIDED with acceptance recorded, PARTIAL with the deferred part tracked by a named step, or PARITY CLEARED with the cutover still deferred. DEFERRED items stay `[ ]` until their trigger fires.

---

## Final V1 plan at a glance

**What V1 is:** nine backend modules (`identity`, `consent`, `vault`, `documents`, `profile`, `catalog`, `applications`, `locker`, `audit`), one service pack (e-District income certificate), a Next.js PWA, and Assist-only preparation — the citizen always submits on the official portal.

**Where it stands:** code-complete V1 plus the security-hardening batch is reached, and Track B is closed — the WP4–WP7 build, the cleanup train, the checklist snapshot, item 8, the six hardening PRs, PostgreSQL parity (#64), the containerized demo (#65) and the 2026-11-19 train (#67–#73: the PDF deadline, apostrophe-friendly reading, ungated draft deletion with its consent-gate affordance, the docker and manual-e2e CI jobs, a browser journey and the WP2 paperwork) are merged and green (**280 backend / 55 web** across 14 files, `main` @ `ac8aa27`). Next is the hosted-pilot gate (host selection, deploy config), blocked on the WP2 gates; inside WP2 only the external qualified legal review remains.

| Phase | What closes it | State |
|---|---|---|
| **0. Cleanup train** | `fix/v1-cleanup-batch` merged (items 17, 26, 29, 73–80) + item 8 | **DONE — merged as `059f678` and `9ec25cc` (2026-11-17)** |
| **1. Code-complete V1** | Gate green on `main` after the merge; checklist snapshot in `docs/planning/` | **DONE — snapshot merged as `f7ab071` (#55); item 8 merged as `9ec25cc` (#56); gate green on `main`** |
| **1b. Security hardening batch** | Six PRs (items 91, 93–99): income prefix-negatives, input caps + retry limit + dev-signin opt-in, traceback redaction, body-limit middleware, bounded PDF parsing, web CSP | **DONE — merged 2026-11-18 as `4525f8c`, `4eb46b4`, `8f7f21f`, `5315df9`, `f2f8a9d`, `df27f11`; gate green at 267 backend / 54 web** |
| **2. Local demo** | App Dockerfiles + full compose stack (Postgres 16, Redis 7, backend, web); smoke flow runs locally | **DONE — merged 2026-11-18 as `89b4be9` (#64) and `d9c0474` (#65); smoke verified twice from clean volumes (default ports) plus one custom-port run; evidence in `docs/evaluation/local-demo-smoke.md`** |
| **3. Hosted pilot** | Host chosen, deploy config, PostgreSQL parity verified, legal/privacy + security gates cleared | Blocked on gates and host |
| **4. Post-pilot** | Trigger-gated work (Part 6) and master-plan tracks (Part 11) | Not scheduled |

**Launch rule:** nothing is hosted with real documents until the WP2 legal/privacy and security gates clear; the pilot stays synthetic-only until then.

---

## Part 1 — Foundations & delivery guardrails

- [x] **1. Monorepo layout** — `backend/` (FastAPI), `apps/web/` (Next.js), `catalog/` (service packs), `infra/`, `scripts/`, `docs/`. *Status: DONE.*
- [x] **2. ADR-0001 modular monolith** — one deployable, modules separated by responsibility. *Status: DONE.*
- [x] **3. ADR-0002 SQLite for dev/test** — local runs and CI are SQLite-only. *Status: DONE (production cutover is item 53).*
- [x] **4. ADR-0003 V1 module scope** — V1 ships 9 modules; `execution`/`integrations` and the compliance resolver are post-pilot; Assist-only. *Status: DONE — PR #51 merged (`0b3a38d`, 2026-11-16).*
- [x] **5. CI gate** — backend: ruff + pyright + pytest (Python 3.14); web: eslint + `next typegen` + tsc + vitest + production build (Node 24). Same gate locally via `scripts/check.sh`. *Status: DONE.*
- [x] **6. Supply chain** — CodeQL on push/PR, Dependabot (pip/npm/actions), actions pinned, `pip-audit` and `npm audit` steps in CI. *Status: DONE.*
- [x] **7. `protect-main` ruleset** — required checks (backend + web) block direct pushes to `main`. *Status: DONE.*
- [x] **8. Onboarding scripts** — `bootstrap.sh`/`check.sh`/`dev.sh`. *Status: DONE — PR #56 (`6647cc9`) merged as `9ec25cc` (2026-11-17): `bootstrap.sh` now runs `RINAVI_ENVIRONMENT=development "$PYTHON" -m alembic upgrade head`, so a fresh clone gets the schema. The env var is required — `migrations/env.py` calls `get_settings()`, which rejects an unset environment. Gate green (234 backend, 50 web); verified against a temp database (all migrations apply, 12 tables). `dev.sh` already sources `scripts/venv.sh` (since #26) and remains a bash script by design.*

---

## Part 2 — Platform security & privacy core

- [x] **9. Environment fails closed** — unset `RINAVI_ENVIRONMENT` is an error that names the variable; production rejects dev sign-in, insecure cookies, non-HTTPS WebAuthn. *Status: DONE (`config.py::_reject_unsafe_production`).*
- [x] **10. Browser security headers** — `nosniff`, `DENY`, `no-referrer`, `Permissions-Policy`, COOP on every response; HSTS in production; 429s and preflights included. *Status: DONE.*
- [x] **11. API docs hidden in production** — `/docs`, `/redoc`, `/openapi.json` unregistered when `environment=production`. *Status: DONE.*
- [x] **12. Rate limiting** — per-IP 1200/hour + per-session 200/hour + per-route tightenings (dev-signin 5/min, passkey begin 10/min, finish 20/min, upload 30/hour, content 100/hour, export 20/hour). Health probes exempt. *Status: DONE. Note:* `memory://` storage = single worker only (see item 57). Session-budget 429s lacked `Retry-After`; fixed in `31b8cf9`, merged via PR #54 (`059f678`, item 79).
- [x] **13. Audit log with redaction** — document contents and PII never reach logs; SHA-256 digests preserved. *Status: DONE, with a gap fixed on PR #54:* consent grant/withdraw and identity sign-in/out/passkey routes emitted no audit events; `9c081a5` adds them with tests; merged via PR #54 (`059f678`, item 78).
- [x] **14. Consent, deny-by-default** — four purposes (`documents.processing`, `profile.storage`, `applications.preparation`, `locker.tracking`) enforced as dependencies on the routes that need them. *Status: DONE.*
- [x] **15. Consent withdrawal** — `/consent` page lists all four purposes and withdraws an active grant; re-grant withdraws prior active grants. *Status: DONE.*
- [x] **16. Authentication** — dev sign-in (dev only), passkey (WebAuthn) sign-up and sign-in, secure session cookie with TTL, sign-out. *Status: DONE.*
- [x] **17. Consent purpose validation** — an empty `purpose` string was accepted (201) because the schema had `max_length` but no `min_length`. *Status: DONE — PR #54 (`642e140`) merged (`059f678`, 2026-11-17): `strip_whitespace=True, min_length=1`; tests reject both `""` and `"   "`.*

---

## Part 3 — The nine modules of V1

### 3.1 identity

- [x] **18. Session management** — cookie session, `get_current_user` dependency, `/auth/me`. *Status: DONE.*
- [x] **19. Passkey flows** — sign-up, login begin/finish, user verification required. *Status: DONE. Note:* the pending-challenge store is per-process — fine for a single worker.*
- [ ] **20. Account export completeness** — `/auth/export` returns only `user` + consent records; document metadata and profile values are missing, so "take your data with you" is not yet true. *Status: DEFERRED — accepted as a pilot limitation; trigger: before the public promise "export your data" is made.*

### 3.2 consent

- [x] **21. Grant / list / withdraw endpoints + UI page.** *Status: DONE (PR #34).*
- [x] **22. Enforcement** — `ConsentRequired` dependency, including `applications.preparation` on locker apply-again (the earlier bypass is fixed). *Status: DONE (PR #31).*
- [x] **23. Duplicate grants** — re-granting a purpose withdraws the previous active record. *Status: DONE.*

### 3.3 vault

- [x] **24. Upload** — 10 MB cap (413), content-type sniffing (415), PDF/PNG/JPEG/TXT. *Status: DONE.*
- [x] **25. Blob lifecycle** — rollback discards stored bytes; delete erases the file before the row and returns 503 (retryable) if the unlink fails. *Status: DONE (PR #30).*
- [x] **26. List / get / delete / content / fields / retry endpoints** — all consent-gated. *Status: DONE, with a gap fixed:* `/documents/{id}/content` read storage unguarded; `54c5889` returns 404 for a missing blob; merged via PR #54 (`059f678`, item 75).
- [x] **27. Download safety** — ASCII-safe filename fallback for Devanagari names, RFC 5987 `filename*`, header injection sanitised. *Status: DONE.*

### 3.4 documents

- [x] **28. Extraction** — 7 fields (`full_name`, `father_name`, `date_of_birth`, `gender`, `address`, `annual_income`, `aadhaar_number`) with line locators and confidence. *Status: DONE.*
- [x] **29. Normalisation correctness** — rupee amounts keep rupees (`Rs 120,000.00` → `120000`); impossible dates stay raw at low confidence; lakh/crore amounts stay raw at low confidence. *Status: DONE (PR #30). Residual:* negative amounts (e.g. `(5,000)`) normalised to positive; `f888223` keeps them raw at low confidence, merged via PR #54 (`059f678`, item 77). Prefix forms such as `Rs -5,000` were fixed in 4525f8c (item 91, 2026-11-18) — item 91 is closed.
- [x] **30. Classification** — `income` / `identity` / `residence` / `unsupported`. *Status: DONE.*
- [x] **31. Failure states** — `content_unavailable`, `ocr_not_configured`, `no_text_layer`, `extraction_failed`, `no_fields_detected` — no 500s from parser or normaliser crashes. *Status: DONE.*
- [x] **32. OCR** — images return `needs_attention` / `ocr_not_configured`. *Status: DECIDED — V1 is PDF/TXT only; pilot script must say so. Trigger: an OCR milestone would reopen this.*
- [ ] **33. Async processing** — `process_document` still runs inline inside the upload request; a large PDF is parsed while the request is held open. *Status: DEFERRED — accepted for synthetic pilot; trigger: real documents or slow uploads in practice.*

### 3.5 profile

- [x] **34. Value lifecycle** — promote from documents, confirm / correct / reject, stale marking when a source document is deleted. *Status: DONE.*
- [x] **35. A1 — Aadhaar portal-only** — restricted fields stay out of profiles, drafts, packets, logs and UI (extraction/redaction untouched): `app/core/privacy.py`, profile read-filters, applications snapshot/value/validation/export/packet filters, vault `/fields` filter, fields with `format: "aadhaar"` hidden even without a profile binding (commit `5747e82`), UI label removed, and the **irreversible Alembic migration** `b7e4f1a2c9d3` deleting legacy `aadhaar_number` profile rows. *Status: DONE — PR #52 merged (`5343719`, 2026-11-16). Verified: `restricted_field` → 422; no phantom required-field issues; 7 new tests (225 total); CI green; web app has zero Aadhaar references. Known residual: legacy draft JSON may retain restricted values written before A1 — never exposed and not clearable via the API; accepted for the synthetic pilot (no current pack emits an Aadhaar field), tracked at item 81.*
- [ ] **36. Aadhaar Verhoeff checksum** — extraction accepts any 12 digits. *Status: DEFERRED — moot under A1 (values never reach profiles); trigger: if Aadhaar handling ever returns to RINAVI.*

### 3.6 catalog

- [x] **37. Service packs** — service list, versioned packs, latest-version resolution. *Status: DONE.*
- [x] **38. Pack integrity gate** — loader rejects a checklist group naming an unknown classification; version strings that escape the service directory are refused. *Status: DONE (PRs #24, #30).*

### 3.7 applications

- [x] **39. Drafts** — create / list / get / refresh / delete with template snapshots. *Status: DONE. Residual:* the list endpoint used an N+1 query pattern; `4e0cdda` batch-loads profile/documents, merged via PR #54 (`059f678`, item 76).
- [x] **40. Field values** — set/clear fields, profile-origin values, citizen overrides. *Status: DONE.*
- [x] **41. Evidence linking** — link/unlink processed documents per checklist group, classification-match enforcement. *Status: DONE.*
- [x] **42. Validation** — per-draft validation issues (missing fields/evidence, declaration). *Status: DONE.*
- [x] **43. Export & packet** — text export and packet snapshot with "NOT a submission" notice, official-channel steps, portal-down and acknowledgement guidance. *Status: DONE.*
- [x] **44. Malformed data tolerance** — malformed document IDs in stored JSON report `unavailable` instead of crashing. *Status: DONE (PR #19).*
- [x] **45. Compliance resolver** — deciding whether a pack's requirements can be met. *Status: DECIDED — V1 is Assist-only and the portal is authoritative; the resolver is post-pilot and additive per ADR-0003. Accepted by merging #51/#53. Trigger: a resolver is scheduled; any resolver must stay advisory.* Note: the master plan's **Compliance Gate** (Assist / Guided / Official execution modes) is a separate decision tracked at item 90; V1 hardcodes Assist.

### 3.8 locker

- [x] **46. Case tracking** — list/get cases, event recording (submitted, acknowledged, outcome, deadline) with audit events. *Status: DONE.*
- [x] **47. Apply-again** — fresh draft from profile + documents, suggested links, requires `locker.tracking` **and** `applications.preparation` consent. *Status: DONE (PR #31).*

### 3.9 audit

- [x] **48. Event emission** — uploads, deletes, draft/field/declaration actions, locker events, apply-again. *Status: DONE.*
- [x] **49. Redaction** — no document content or PII in logs; SHA-256 digests kept for correlation. *Status: DONE (PR #17).*

---

## Part 4 — WP8 pilot readiness (deferred ledger + decisions)

The gate: every deferred item is cleared or explicitly accepted. This is the **code-side** WP8 ledger gate; the pilot operating plan and launch tracks are Part 11 (items 82–90).

- [x] **50. Readiness document** — `docs/compliance/wp8-pilot-readiness.md` exists and is checked against code, not the ledger. *Status: DONE (PR #35, refreshed #49 and #53).*
- [x] **51. Readiness "Decisions recorded" rewrite** — replace "Decisions needed" with the recorded table + reopen triggers; update "Found after WP7" items; link ADR-0003. *Status: DONE — PR #53 merged (`e49405b`, 2026-11-16). All 10 decisions and reopen triggers recorded; README test count updated 218→225; honest "did not verify" section. Merged last, after #50/#51/#52.*
- [x] **52. Encryption at rest** — *Status: DECIDED — accepted for the synthetic-only pilot. Trigger: real documents → plaintext `.bin` storage is the largest exposure and must be solved first.*
- [x] **53. PostgreSQL cutover** — *Status: PARITY CLEARED — PR #64 (`89b4be9`, 2026-11-18) added `asyncpg` and a `backend-postgres` CI job that runs the full suite against PostgreSQL 16 (268 passed); Alembic `upgrade head` and `alembic check` verified; the compose demo runs the backend on PostgreSQL. The production cutover itself stays deferred (ADR-0002 deviation accepted). Trigger: real data or a chosen pilot host; the cutover config (item 67) must land before either.*
- [x] **54. Retention sweeps** — no scheduler exists. *Status: DECIDED — deferred. Trigger: real documents (deletes are retryable today, so nothing is permanently orphaned by design).*
- [x] **55. Extraction cost baseline** — extraction is deterministic (regex/rules): no LLM, pgvector, Tesseract or Document AI anywhere in the repo, so spend is zero. *Status: DONE by absence; nothing to meter yet. Trigger: any inference dependency is added.*
- [x] **56. Real documents** — *Status: DECIDED — out of scope until the legal/privacy review and security gate complete; everything in dev/tests is synthetic.*
- [x] **57. Deployment topology** — *Status: DECIDED — single worker, `memory://` rate-limit storage stays. Trigger: multi-worker or autoscaling → shared Redis backend (`redis` extra already declared).*
- [x] **58. Pilot host / Dockerfile** — *Status: PARTIAL — the demo stack landed via PR #65 (`d9c0474`, 2026-11-18): backend and web Dockerfiles (non-root UID 10001, migrations-before-uvicorn, Next standalone), a full `infra/compose` app stack (Postgres 16, Redis 7, backend, web, loopback-only ports), and a 14-step smoke of the citizen flow, verified twice from clean volumes (default ports) plus one custom-port run. Host selection remains deferred until the WP2 gates clear (Part 10 step 13).*
- [x] **59. OCR scope** — *Status: DECIDED — PDF/TXT only; stated in the pilot script.*

---

## Part 5 — The four-PR build plan (merged 2026-11-16)

Execution order, one by one:

- [x] **60. PR 1.1 — minimatch advisory (#41)** — `eslint` → `^10.15.0` + scoped override `@typescript-eslint/typescript-estree.minimatch` → `^11.0.5`. *Status: DONE — PR #50 merged (`49aa812`, 2026-11-16). Full `npm audit` reports 0; CI's `npm audit --omit=dev` cannot see this dev-only advisory. Close issue #41 after the Dependabot rescan.*
- [x] **61. PR 1.3 — V1 module scope ADR** — `docs/architecture/decisions/0003-v1-module-scope.md`. *Status: DONE — PR #51 merged (`0b3a38d`, 2026-11-16). Merging it accepted the resolver as post-pilot (item 45).*
- [x] **62. PR 1.4 — A1 portal-only** — item 35 above. *Status: DONE — PR #52 merged (`5343719`, 2026-11-16). Irreversible legacy-row migration included and test-covered.*
- [x] **63. PR 1.2 — readiness final** — item 51 above. *Status: DONE — PR #53 merged (`e49405b`, 2026-11-16), last in the order.*

---

## Part 6 — Explicitly out of V1 (honoured, untouched)

With reopen triggers:

- [ ] **64. Encryption at rest / object storage** — trigger: real documents (item 52).
- [ ] **65. Export completeness** — trigger: before promising "take your data with you" (item 20).
- [ ] **66. Compliance resolver** — post-pilot and additive per ADR-0003; V1 is Assist-only (item 45). Trigger: a resolver is scheduled.
- [ ] **67. PostgreSQL production cutover** — trigger: real data (item 53).
- [ ] **68. Retention sweeps** — trigger: real documents (item 54).
- [ ] **69. Async worker / threadpool offload** — trigger: real documents or slow uploads (item 33).
- [ ] **70. OCR implementation** — trigger: image-evidence requirement (item 32).
- [ ] **71. Pagination, fetch timeouts, delete confirmations, new features** — trigger: named by a future work package.
- [ ] **72. Aadhaar extraction/redaction changes** — explicitly untouched; A1 only removes propagation, and the Verhoeff checksum stays deferred (item 36).
- [ ] **81. Legacy draft JSON scrub** — drafts written before A1 may retain restricted values in `application_drafts.values`; they are never exposed and cannot be cleared via the API. Accepted for the synthetic pilot (no current pack emits an Aadhaar field). Trigger: real documents or an Aadhaar-bearing pack → add an irreversible scrub migration.

---

## Part 7 — Open bugs & residuals to tackle one by one

Small, concrete, each with a RED test first:

- [x] **73. CORS example uses a non-JSON value** — `backend/.env.example:17` has the CORS line commented; uncommenting it as-is raises `SettingsError` because the setting expects a JSON array. *Fix:* `RINAVI_CORS_ORIGINS=["http://localhost:3000"]`. *Status: DONE — `2d608eb`, merged via PR #54 (`059f678`, 2026-11-17).*
- [x] **74. Empty consent purpose accepted** — add `min_length` (or purpose allow-list) to `consent/schemas.py` (item 17). *Status: DONE — `642e140`, merged via PR #54 (`059f678`, 2026-11-17).*
- [x] **75. Missing blob → 500 on content download** — guard `storage.read` in `vault/routes.py::document_content`; return 404/410 matching the pipeline's `content_unavailable` state. *Status: DONE — `54c5889` returns 404 with an integration test; merged via PR #54 (`059f678`, 2026-11-17).*
- [x] **76. N+1 on drafts list** — `applications/routes.py::list_drafts` called `draft_out` per draft; `4e0cdda` batch-loads profile and document queries with a query-count regression test. *Status: DONE — merged via PR #54 (`059f678`, 2026-11-17).*
- [x] **77. Negative income normalisation** — `_normalize_income` turns `(5,000)` / `-5000` into positive `5000` at high confidence; keep negatives raw at low confidence. *Status: DONE — `f888223` keeps them raw at low confidence, merged via PR #54 (`059f678`, 2026-11-17). Prefix forms were fixed in 4525f8c (item 91, 2026-11-18).*
- [x] **78. Missing audit events** — consent grant/withdraw and identity sign-in/out/passkey routes emitted no audit events. *Status: DONE — `9c081a5` adds `emit_audit` calls and tests; merged via PR #54 (`059f678`, 2026-11-17).*
- [x] **79. Session 429s report a zero Retry-After** — session-budget 429s were injected with the IP limiter, whose store never saw the session key, so the header said `0` (retry immediately) instead of the remaining window. *Status: DONE — `31b8cf9` injects with the budget that tripped, with a regression test; merged via PR #54 (`059f678`, 2026-11-17).*
- [x] **80. `wp8-aadhaar-a1` stale branch** — was at `0f80f19`, an ancestor of `main` with zero unique commits. *Status: DONE — deleted 2026-11-17 along with the five merged PR branches; all remote feature branches are gone.*
- [x] **91. Prefix-negative income forms** — `_normalize_income` only catches a leading `-` or an exact `(...)` wrapper, so `Rs -5,000`, `INR -5000`, `Rs. (5,000)` and `(5,000) approx` still normalise to `5000` at high confidence (verified during the PR #54 review). *Status: DONE — hardening PR 1 (`fix/income-prefix-negatives`) merged as `4525f8c` (2026-11-18): prefix-aware negative detection plus tests, extending item 77. Residual: a few uncommon negative forms still stay at low confidence; non-blocking.*
- [x] **92. Compose object-storage reference is dead upstream** — `minio/minio:latest` is no longer publicly pullable: the Docker Hub repository returns 404, `docker manifest inspect` returns `denied / authentication required` for `latest` and for old `RELEASE.*` tags, `minio/mc` is the same, and `quay.io/minio/minio` returns 401. MinIO now publishes only AIStor (registration/paid). *Status: DONE — Option A recorded (2026-11-18): MinIO is dropped from the compose stack, which runs Postgres 16, Redis 7, backend and web only. The backend uses `LocalDiskStorage` and has no S3 client. Object storage remains owned by item 64 (trigger: real documents), which may reintroduce a maintained S3-compatible service.*
- [x] **93. Length caps on unbounded request strings** — `FieldUpdateIn.value`, `DraftCreateIn.service_slug`, `DocumentLinkIn.group_id`, `PasskeyFinishRequest.challenge_id`/`credential` have no max lengths, so absurd payloads reach the DB/handlers. Cap them (500 / 80 / 80 / 128 / 16 KiB), with unit and API-level 422 tests. *Status: DONE — hardening PR 2 (`fix/request-input-bounds`) merged as `4eb46b4` (2026-11-18): caps on all four fields with unit and API-level 422 tests.*
- [x] **94. Rate-limit the retry endpoint** — `POST /vault/documents/{id}/retry` re-parses a PDF with no per-route budget, unlike upload. Give it the upload budget (`UPLOAD_LIMIT`, `session_or_ip`) so a citizen cannot re-parse past 30/hour; test the 31st retry returns 429 with a positive `Retry-After`. *Status: DONE — hardening PR 2 (`fix/request-input-bounds`) merged as `4eb46b4` (2026-11-18): the retry route uses the upload budget; the 31st retry returns 429 with a positive `Retry-After`.*
- [x] **95. Traceback redaction** — `RedactingFilter` scrubs `record.msg` only; a logged exception with an email or 12-digit run in its message would reach the formatted traceback untouched. Format `exc_info` through `redact_text` into `record.exc_text` (clear `exc_info`), redact `stack_info` too; tests for `[REDACTED]` plus UUID/SHA-256 survival. *Status: DONE — PR #59 (`fix/redact-tracebacks`) merged as `8f7f21f` (2026-11-18): `exc_info`/`stack_info` are redacted, and the filter also attaches to `uvicorn`/`uvicorn.error`/`uvicorn.access` handlers with a behavioural `dictConfig` test.*
- [x] **96. Dev sign-in becomes explicit opt-in** — `dev_signin_enabled` currently defaults to `True`, so a forgotten env file ships a sign-in bypass. Default it to `False`; `scripts/dev.sh` and `tests/conftest.py` set `RINAVI_DEV_SIGNIN_ENABLED=true`; `.env.example` and the README explain it; the production rejection stays. The phase-2 Docker backend service must set `RINAVI_DEV_SIGNIN_ENABLED=true` for the demo (and must never set it in the hosted-pilot config). *Status: DONE — hardening PR 2 (`fix/request-input-bounds`) merged as `4eb46b4` (2026-11-18): `dev_signin_enabled` defaults to `False`; `scripts/dev.sh` and the test fixture opt in; `.env.example` and the README explain it; production still rejects it.*
- [x] **97. Request-body cap middleware** — no global cap exists, so a large JSON/plain body is read into memory before any handler. Pure-ASGI middleware wrapping `receive`: 1 MB for JSON, 11 MB otherwise, JSON 413 on overflow, registered before the rate limiter so 413s carry CORS/security headers and don't consume budget. Tests: 2 MB JSON → 413, chunked oversize → 413, 10 MB multipart upload → 201, 10 MB + 1 → 413. *Status: DONE — hardening PR 4 (`feat/request-body-limit`) merged as `5315df9` (2026-11-18). Pilot residual: add reverse-proxy body/read timeouts before the hosted pilot.*
- [x] **98. Bounded PDF parsing off the event loop** — `extract_text_from_pdf` has no page/text caps and runs synchronously on the event loop, so one hostile PDF can stall the single worker. Cap pages (100) and text (2 MB) with early stop; run extraction via `asyncio.to_thread`; oversize documents land in `needs_attention` with `page_limit_exceeded` / `text_limit_exceeded` notes. *Status: DONE — hardening PR 5 (`fix/bounded-pdf-parsing`) merged as `f2f8a9d` (2026-11-18). Pilot residual: PR #67 adds a 20 s deadline checked between pages, but `PdfReader` construction and a single `extract_text()` call remain unbounded; add a worker-level kill timeout or process isolation before the hosted pilot.*
- [x] **99. CSP on the web app** — static policy in `next.config.ts` (`default-src 'self'`, `script-src`/`style-src` with `'unsafe-inline'` for the Next runtime, `img-src 'self' data:`, `connect-src 'self' <API origin>`, `frame-ancestors 'none'`, `base-uri`, `form-action`), with a unit test asserting the policy string and the configured API origin. *Status: DONE — PR #62 (`feat/web-csp`) merged as `df27f11` (2026-11-18): static policy in `next.config.ts`; `script-src` adds `'unsafe-eval'` only when `NODE_ENV === "development"` (React's dev error stacks need it; production stays without it), with both modes unit-tested. `NEXT_PUBLIC_API_URL` is build-time input; rebuild the web image per environment.*

---

## Part 8 — Steps for completing any open item

Standard flow (used by every PR so far):

1. `git switch main && git pull --ff-only origin main` — always start from synced `main`.
2. Create a branch: `chore/…`, `fix/…`, `feat/…`, `docs/…` depending on the item.
3. **Code items:** write the failing test first and watch it fail (RED), implement the smallest fix (GREEN), then run the whole gate (REFACTOR). **Doc/config items:** no tests needed, but the gate still runs.
4. Run `scripts/check.sh` — backend: ruff, pyright, pytest; web: eslint, typegen, tsc, vitest, build. Exit 0 required.
5. For migration changes: run `alembic upgrade head` against a copy of the database and verify the result manually. Most tests build the schema from metadata, but `tests/test_migrations.py` runs Alembic `upgrade head` and `alembic check`; data migrations still need the DB-copy check.
6. Commit per item, push, open a PR using the repo's PR template (Summary / Type / How tested / Security & privacy checklist / Screenshots), state `Closes #<issue>` where relevant, and confirm CI is green.
7. Squash-merge in the GitHub UI (the human merges; the agent stops at a green PR), then `git pull --ff-only` locally and delete the merged branch.
8. Come back to this checklist: tick the box, update status and date.

---

## Part 9 — Verification commands

```bash
# backend (activate the venv in the same command)
cd backend && source ../scripts/venv.sh && activate_backend_venv .venv \
  && ruff check app tests && python -m pyright && python -m pytest -q

# web
cd apps/web && npm run lint && npx next typegen && npx tsc --noEmit \
  && npm run test -- --run && npm run build

# both at once
scripts/check.sh
```

---

## Part 10 — The final V1 plan, in order

### Now — close the cleanup train (code complete)

1. [x] Run `scripts/check.sh` on `fix/v1-cleanup-batch` — expect green (backend 234, web 50). Passed; CI backend, web and CodeQL are green on `4e0cdda`.
2. [x] Push the branch and open **one PR** covering items 17/74 (blank consent purposes), 26/75 (missing blob → 404), 29/77 (negative income stays raw), 73 (CORS example), 76 (drafts N+1), 78 (audit events), 79 (`Retry-After`) — commits `2d608eb`, `642e140`, `54c5889`, `f888223`, `9c081a5`, `31b8cf9`, `4e0cdda`. Opened as **PR #54**, reviewed with no blocking bugs, and **merged as `059f678` on 2026-11-17**; all checks green.
3. [x] After the merge: pulled `main`, ticked items 17, 26, 29, 73–80, and deleted the six merged local branches.
4. [x] Fix **item 8** — add `alembic upgrade head` to `bootstrap.sh` in its own small PR. *Merged as PR #56 (`9ec25cc`, 2026-11-17).*
5. [x] **Issue #41** is closed (2026-11-16); full `npm audit` reports **0 vulnerabilities**; the stale local branches are deleted (item 80). Spot-check Dependabot alert #1 on the security page once.
6. [x] Snapshot this checklist to `docs/planning/v1-checklist.md`, with the snapshot commit/date, a note that the working copy lives outside the repo, and that `wp8-pilot-readiness.md` stays authoritative. Also update the backend test count (225 → 234) in `README.md` and the readiness doc. *Merged as PR #55 (`f7ab071`, 2026-11-17); branch deleted.*

### Now — security hardening batch (six PRs, in this order)

Approved 2026-11-17 as the follow-up to the cleanup train; each PR was one review surface, merged before the next started. Post-review amendments: #59 also filters uvicorn's own handlers; #62 adds `'unsafe-eval'` to the CSP in development only. **All six merged 2026-11-18.**

1. [x] **Hardening PR 1** — `fix/income-prefix-negatives` (item 91): `Rs -5,000`, `INR -5000`, `Rs. (5,000)`, `(5,000) approx` stay raw at low confidence; scale-word and range cases unchanged. *Merged as `4525f8c`.*
2. [x] **Hardening PR 2** — `fix/request-input-bounds` (items 93, 94, 96): schema caps with unit + API 422 tests; retry endpoint gets the upload budget; `dev_signin_enabled` defaults to `False` with dev/test env vars and docs. *Merged as `4eb46b4`.*
3. [x] **Hardening PR 3** — `fix/redact-tracebacks` (item 95): `RedactingFilter` scrubs `exc_info`/`stack_info` and is attached to uvicorn's own handlers, so `uvicorn.error` tracebacks are covered too. *Merged as `8f7f21f`.*
4. [x] **Hardening PR 4** — `feat/request-body-limit` (item 97): pure-ASGI 1 MB JSON / 11 MB body caps, JSON 413, before the rate limiter. *Merged as `5315df9`.*
5. [x] **Hardening PR 5** — `fix/bounded-pdf-parsing` (item 98): 100-page / 2 MB text caps, `asyncio.to_thread`, defined `needs_attention` notes. *Merged as `f2f8a9d`.*
6. [x] **Hardening PR 6** — `feat/web-csp` (item 99): static CSP in `next.config.ts` with the configured API origin in `connect-src`, plus `'unsafe-eval'` in development only. *Merged as `df27f11`.*

*Close-out (2026-11-18):* the **hardening milestone** closed at `main` @ `df27f11` (local gate green at 267 backend / 54 web, verified locally), ticking items 91 and 93–99 above. The **Track B milestone** then closed at `main` @ `d9c0474` (268 backend / 54 web): PR #64 (`89b4be9`) proved PostgreSQL parity and PR #65 (`d9c0474`) shipped the demo stack; item 92 closed (Option A); see steps 7–11 below.

### Next — local containerized demo (started 2026-11-17)

7. [x] Add `backend/Dockerfile` and `apps/web/Dockerfile` plus `.dockerignore` files. The backend build context must include `catalog/` as well as `backend/` (`catalog/loader.py` resolves `parents[4]/catalog/services`), run as a non-root user, and start through an entrypoint that applies `alembic upgrade head` before uvicorn. *Merged as PR #65 (`d9c0474`, 2026-11-18): both Dockerfiles with `.dockerignore`s, non-root UID 10001, entrypoint applies migrations before uvicorn.*
8. [x] Add a PostgreSQL driver (`asyncpg>=0.32`; cp314 Windows wheels exist) so `postgresql+asyncpg://` works, then turn `infra/compose/compose.yaml` into the full demo stack: `name: rinavi`, Postgres 16, Redis 7, backend, web, vault volume, env template, healthchecks and `depends_on: service_healthy`. The backend service sets `RINAVI_DEV_SIGNIN_ENABLED=true` for the demo (never in the hosted-pilot config), `RINAVI_ENVIRONMENT=development`, and a Postgres `RINAVI_DATABASE_URL`. *Merged as PR #64 (`89b4be9`) for the driver + `backend-postgres` CI job, and PR #65 for the full compose stack; all ports bind to loopback.*
9. [x] Verify from clean volumes: `docker compose up --build` → migrations run → `/api/v1/health` → smoke flow (dev sign-in, upload a synthetic PDF, extract, confirm a profile value, create a draft, validate, export the packet). Also run the backend suite with `RINAVI_TEST_DATABASE_URL=postgresql+asyncpg://rinavi:rinavi@127.0.0.1:5432/rinavi_test` against the compose Postgres (`tests/conftest.py` honors that variable and refuses non-test database names) and add a `backend-postgres` CI job; this is the first half of item 53. Run `docker compose down -v` and repeat once. *Done twice from clean volumes (default ports) plus one custom-port run, smoke 14/14 each time; the custom-port path was independently re-verified from a clean volume by the PR #66 review; backend suite green against the compose Postgres (268). Evidence: `docs/evaluation/local-demo-smoke.md`.*
10. [x] Keep the single worker and `memory://` rate limiting as the default; Redis is provisioned for the later switch (item 57). *Kept as decided; Redis runs in the stack, unused by the limiter.*
11. [x] Correct the README's `infra/compose` description, add a Docker quick start (with the synthetic-only warning and image/OCR caveat), and record the smoke evidence in `docs/evaluation/`. *Done in PR #65, including the custom-port fix (squashed into `d9c0474`) that keeps CORS/WebAuthn origins and the baked API URL in step with `WEB_PORT`/`API_PORT`.*

### Later — hosted pilot (blocked until the gates clear)

12. [ ] Clear the **WP2 legal/privacy gate** and the security gate (items 83, 56).
13. [ ] Choose a host; add deploy config, a CI deploy step and an operations runbook (item 58).
14. [x] **PostgreSQL parity is verified** — PR #64 (`89b4be9`): the full suite passed against PostgreSQL 16 (268), Alembic `upgrade head` and `alembic check` verified, and the compose demo runs the backend on PostgreSQL. The production cutover config itself stays deferred until a real host is chosen (items 53, 67).
15. [ ] Run **WP8 pilot operations** (item 84) and **WP11 launch readiness** (item 85), then launch the controlled synthetic pilot.

Pre-pilot residuals before step 15: reverse-proxy body/read timeouts (item 97) and a PDF parse timeout or process isolation (item 98).

### After the pilot — trigger-gated

16. [ ] Work **Part 6** items when their triggers fire.
17. [ ] Work **Part 11** master-plan tracks only when the evidence gates justify them.

---

## Part 11 — Master-plan tracks outside the V1 build

From `docs/superpowers/plans/2026-11-09-rinavi-structured-build.md` (WP1–WP12). These are real launch and roadmap work, but none of it belongs to the nine-module code-complete build, and none of it is started.

- [ ] **82. WP1 — discovery evidence** — 20–30 citizen interviews, service scorecard, service/geography selection, baseline metrics. *Gate: blocks WP8 and any expansion.*
- [ ] **83. WP2 — legal/privacy gate** — data map, consent and retention policy, portal-permission register, threat model, qualified legal review. *Status: ARTEFACTS DRAFTED AND MERGED; GATE OPEN ON THE QUALIFIED REVIEW — eight documents in `docs/compliance/` (`pilot-plan.md`, `data-map.md`, `privacy-notice-draft.md`, `terms-draft.md`, `retention-policy.md`, `recording-consent.md`, `portal-permission-register.md`, `threat-model.md`) on `main` @ `fee4e9f`, merged as #73 (`ac8aa27`), plus a one-page brief for you in `reviewer-brief.md`. The box stays unticked because the **qualified legal review** has not happened — it is not a repository change, and real documents and any hosted pilot stay blocked until it signs off. Three questions are with the reviewer: case completion under `applications.preparation` alone, promotion under `profile.storage` alone, and erasure coverage for cases and confirmed profile values; draft deletion is ungated (#71) and reachable from the consent gate (#72). The eight risks accepted for synthetic data only, with their reopen triggers, are in the brief and in `threat-model.md` §6.*
- [ ] **84. WP8 — pilot operations** — pilot protocol, cohort definition, support runbook, rule-update runbook, measurement definitions. The code-side ledger is Part 4; this is the operating plan.
- [ ] **85. WP11 — launch readiness** — accessibility audit, responsive/low-bandwidth check, browser/E2E journeys (one manual Playwright journey exists, merged as #70; coverage is still thin), backup/restore drill, incident response, unit economics, pricing experiments.
- [ ] **86. WP9 — second service** — domicile certificate first, then NSP and CPGRAMS, each behind its own evidence gate. Trigger: WP1/WP8 evidence from the income-certificate pilot.
- [ ] **87. WP10 — guided-fill extension** — restricted Manifest V3 extension plus one permitted portal adapter; needs its own security review. Trigger: an approved portal-permission register (item 83).
- [ ] **88. WP12 — Resolve** — error taxonomy, recovery playbooks, CPGRAMS grievance preparation, escalation paths. Post-pilot and advisory only.
- [ ] **89. DigiLocker integration** — approval-gated retrieval/verification track. Trigger: partner approval plus a legal review of the consent flow.
- [ ] **90. Compliance Gate / `execution` module** — WP7's Assist/Guided/Official execution-mode decision is separate from the eligibility resolver (item 45). V1 hardcodes Assist; adding Guided or Official needs a new ADR, the `execution` module, and portal-permission evidence.
