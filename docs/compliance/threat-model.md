# Threat model — V1, synthetic pilot

**Status:** draft for the WP2 legal/privacy review. **Date:** 2026-11-19,
against `main` @ `fee4e9f`.
**Companion to:** `data-map.md` (what exists and where), `portal-permission-register.md`
(what the system may do with a portal), `retention-policy.md` (what outlives
deletion). **Authority:** `wp8-pilot-readiness.md` stays authoritative for
compliance decisions. Neither is legal advice.

**Public copy:** this document names residual risk *categories*, not the specific
missing controls or exploit paths. The detailed residual register is supplied to
the qualified reviewer separately.

## 1. Scope and method

This models the deployment actually used for phase A: the compose stack (or the
dev servers) on one machine, reachable at loopback, with one facilitator and
10–20 participants. It is a **narrow** threat model on purpose. Hosting, a public
domain, more than one worker and real documents each change the answer, and each
is listed in §7 as a trigger to redo this document.

Method: list the assets, list who could touch them, draw the boundaries between
them, then for each realistic threat name the control that exists *in the code*
and the residue that remains. A control with no file or test next to it is
treated as missing, not as assumed.

The single most important structural fact: **no request leaves the deployment.**
There is no outbound HTTP client in the runtime dependency set, no portal
adapter, no email, no analytics, no inference API (`pyproject.toml`;
`data-map.md` §5). That removes a whole class of threats — SSRF, credential
relay, third-party data sharing — by construction rather than by policy, and it
is why §5 has no SSRF row and §6 lists no processor.

## 2. Assets

Ordered by what the pilot would have to stop for.

| # | Asset | Where | Impact if disclosed | Impact if lost or altered |
|---|---|---|---|---|
| A1 | Document bytes | `<storage_dir>/<user_id>/<document_id>.bin`, AES-GCM ciphertext (item 101) | Total for that participant: the whole document | Unrecoverable; no backup |
| A2 | Extracted field values; an `aadhaar_number` line is stored as `[REDACTED]` | `extracted_fields` | High: structured identity data; no Aadhaar digits survive here | Re-derivable from A1 |
| A3 | Profile values and draft values | `profile_values`, `application_drafts` | High: name, address, income, date of birth, father's name | Participant re-enters by hand |
| A4 | Case packets and reference numbers | `application_cases.packet_text`, `case_events` | High: the assembled application plus portal references | Tracking history lost |
| A5 | Accounts and sessions | `users`, `sessions` | Medium-high: email + a working session is the account | Participant re-enrolls |
| A6 | Consent history | `consent_records` | Medium: purpose and timestamps | Loss of the proof of what was agreed |
| A7 | Audit trail | `audit_events` | Low: actions, UUIDs, redacted details | Loss of the security record |
| A8 | Pilot folder — notes, recordings | Outside the system, facilitator's machine | High: unscripted interview content | Findings lost |

Integrity matters less than confidentiality here: the product's output is a
draft the citizen reads and files themselves, so a tampered draft is caught by
the person it belongs to. The integrity that *does* matter is the consent record
(A6) and the audit trail (A7), because they are the evidence of what happened.

## 3. Actors

| Actor | Capability | Motive |
|---|---|---|
| Participant (legitimate) | Own account, own browser, scripted session | Use the product; may paste real data by mistake |
| Participant (curious) | Own account plus devtools; knows another participant | See someone else's data, or the facilitator's screen |
| Anonymous internet | Can reach the port *if* it is exposed; today it is loopback only | Scan, probe, automated attack |
| Facilitator / insider | OS account running the backend: full database and vault access, filesystem, logs | Curiosity, accident, coercion |
| Thief or finder of the laptop | The disk, if unencrypted | The data on it |
| Future contributor | Commits code | Ship a feature that quietly changes a boundary |
| Dependency or CI attacker | Build inputs | Supply-chain compromise |

The facilitator is treated as an **insider threat**, not as trusted staff. There
is no admin panel and no staff role, so the facilitator's power is exactly the
power of the OS account — which is the honest way to describe it.

## 4. Trust boundaries

```
 [ participant browser ] --B1-- [ web (Next) + API (FastAPI) ] --B2-- [ database ]
                                          |
                                          +--B3-- [ vault directory, AES-GCM blobs ]
                                          |
                                          +--B4-- [ logs / stdout ]

 [ facilitator ] --B5-- [ OS account: database file, vault, logs ]
 [ pilot folder, notes, recordings ] --B6-- (outside the system entirely)
 [ portal ] ......B7...... (does not exist: no connection)
 [ CI / npm / pip ] --B8-- [ build outputs ]
```

- **B1** is loopback during phase A, so it is not a network boundary yet. It
  becomes one the moment the pilot is hosted; every B1 control was written for
  that case anyway (headers, CORS, rate limits, TLS-only cookies in production).
- **B2** and **B3** are same-machine boundaries between the app and its data.
  They stop application-level attacks (a route, a query) but not the OS user.
- **B5** is the boundary this model cannot defend: the facilitator *is* the OS
  user. Everything in §6 about insiders flows from that.
- **B7** is deliberately absent. `portal-permission-register.md` records that
  absence as the product's design, and P5 there is the reason it stays.

## 5. Threats and controls

Each row names the control that exists and where it is; a row with "none" in the
control column would be a finding, and there are none of those — the findings
are the residuals.

### 5.1 Access to other people's data

| ID | Threat | Control | Where |
|---|---|---|---|
| T1 | **IDOR** — a participant requests another participant's document, draft, case or profile value by guessing a UUID | Every read and write resolves ownership from the session's `user_id`, never from a request parameter; a foreign or unknown id returns 404, not 403, so existence is not confirmed | `vault/service.py::get_own_document`, `applications/service.py::get_own_draft`, `locker/service.py`; `tests/integration/test_documents_api.py`, `test_locker_api.py`, `test_applications_api.py` |
| T2 | **Cross-account write** — deleting or modifying someone else's row | Same scoping; both ungated draft-erasure routes resolve through the owner-scoped lookup — the single delete by id, the collection delete through `list_drafts(db, user)` — covered by `test_draft_deletion_is_owner_scoped_without_consent_gate` and `test_delete_all_drafts_is_owner_scoped_and_idempotent` | `applications/routes.py::delete_draft`, `delete_all_drafts` |
| T3 | **Account enumeration** — learning whether an email is registered | Passkey login answers `Unknown credential` only after a credential lookup, and the demo sign-in is a dev-only route; no password reset, no "email already in use" flow | `identity/routes.py`; residual §6.6 |
| T4 | **Horizontal read via the export** | `/auth/export` is session-scoped and returns only that user's row and consent records, `Cache-Control: no-store, private`, 20/hour | `identity/routes.py::export_account` |

**Residual:** ownership is enforced per route, so a *new* route that forgets the
owner-scoped lookup is caught by review and tests, not by the type system. There
is no row-level security in the database. A participant who finds a route added
after this model was written is the exposure. Reopen on any new module or route.

### 5.2 Session and browser

| ID | Threat | Control | Where |
|---|---|---|---|
| T5 | **Session theft via XSS** | Cookie is `HttpOnly`, `SameSite=Lax`, `Secure` outside development; CSP is `default-src 'self'` with `connect-src` limited to its own origin and the API origin; no third-party script, no `dangerouslySetInnerHTML` anywhere in `apps/web/src`; React escapes all citizen-supplied text (draft values, case notes, filenames) | `identity/routes.py::set_cookie`, `apps/web/next.config.ts::buildCspPolicy`, `apps/web/src/lib/csp.test.ts`, `tests/integration/test_auth.py::test_session_cookie_is_httponly_and_samesite_lax` |
| T6 | **CSRF** — another site drives a cookie-authenticated mutation | All mutations are `POST`/`PUT`/`DELETE` (never a state-changing `GET`); `SameSite=Lax` stops the cookie riding a cross-site request; CORS allows credentials only from the configured origins; JSON bodies require a preflight the allow-list refuses | `main.py::create_app`, `core/config.py::cors_origins`, `tests/integration/test_cors.py` |
| T7 | **Session fixation or predictable token** | Token is `secrets.token_urlsafe(32)` generated server-side at login; only its SHA-256 is stored, so a database read does not yield a usable token; a token cannot be chosen by the client | `identity/service.py::new_session_token`, `hash_token` |
| T8 | **Stolen device keeps access forever** | Sign-out revokes the row; a session is rejected after `expires_at` (7 days); account deletion clears the cookie | `identity/service.py::get_user_for_token`, `revoke_session` |
| T9 | **Brute force / credential stuffing** | No passwords exist to stuff. Dev sign-in is 5/minute and 404 unless `RINAVI_DEV_SIGNIN_ENABLED`, which production refuses; passkey begin 10/minute, finish 20/minute | `core/rate_limit.py`, `core/config.py::_reject_unsafe_production`, `tests/integration/test_rate_limits.py` |

**Residual:** browser-session hardening is sized for a same-site, single-origin
pilot on loopback, not for a shared registrable domain. Request-integrity,
content-security-policy and session-lifetime improvements are deliberately
deferred to the hosting gate; the specific gaps are kept out of this public copy
and listed in the private review material. Reopen on hosting, on any third-party
script, or on any HTML injection sink. No privilege changes exist that would
require session rotation today.

### 5.3 Untrusted input

| ID | Threat | Control | Where |
|---|---|---|---|
| T10 | **Oversized upload** — disk or memory exhaustion | 10 MB cap enforced after a bounded read (`MAX_UPLOAD_BYTES + 1`), 413 beyond it; magic-byte sniffing rejects anything that is not PDF/PNG/JPEG/TXT with 415, whatever the client claims | `vault/routes.py::upload_document`, `vault/validation.py`, `tests/integration/test_document_pipeline.py` |
| T11 | **Malicious PDF** — parser crash, zip bomb, CPU burn | Page count and extracted-text size are capped (100 pages / 2 MB text); parsing runs off the event loop; a failure parks the document as `needs_attention` instead of 500ing; the retry route shares the upload budget | `documents/pipeline.py`, `documents/extraction.py`, `tests/integration/test_document_pipeline.py` |
| T12 | **Path traversal via filename** | The stored path is built only from server-generated UUIDs — the client filename never touches the filesystem path. The download name is sanitised to ASCII, with quotes, CR/LF and separators dropped, and a UTF-8 `filename*` form used for display | `vault/storage.py::_path`, `vault/routes.py::_safe_download_name`, `_content_disposition` |
| T13 | **Header injection via filename** | Same sanitiser; Starlette would reject CR/LF, and the ASCII fallback removes the bytes before that | `vault/routes.py::_safe_download_name` |
| T14 | **Huge or deeply nested request body** | Pure-ASGI body limit — 1 MB for JSON, 11 MB otherwise — counted across chunked transfers, rejected with 413 **before** the rate limiter, so an oversized body cannot spend the budget | `core/body_limit.py`, `main.py` ordering comment, `tests/integration/test_body_limits.py` |
| T15 | **Mass assignment / writing a portal-only field** | Pydantic request schemas with length caps; draft field ids are checked against the pack; a field bound to a restricted (Aadhaar) binding is rejected with 422; unknown field → 404 | `applications/schemas.py`, `applications/service.py::set_field_value`, `core/privacy.py`, `tests/unit/test_application_builder.py` |
| T16 | **Stored XSS through citizen text** | React text interpolation only; no HTML sink in the web app; the export is rendered as text, not markup | `apps/web/src/features/**` (no `dangerouslySetInnerHTML`) |

**Residual:** the parse deadline is PR #67. It bounds time between pages;
`PdfReader` construction and a single `extract_text()` call remain unbounded, so
a crafted PDF can still hold a request open up to the page/text caps. Parsing
still happens inside the upload request, off the event loop in a worker thread
(readiness ledger item 1), so a slow document ties up a thread and competes for
CPU with other requests — an availability issue that also degrades rate-limit
fairness. Both reclose with a worker-level timeout and an async worker; neither
is a confidentiality risk.

### 5.4 Leakage through logs, audit and storage

| ID | Threat | Control | Where |
|---|---|---|---|
| T17 | **PII in logs** — a document value or email reaching stdout | A redaction filter scrubs email addresses, 12-digit runs (Aadhaar-shaped) and 10-digit runs (phone-shaped), while preserving UUIDs and SHA-256 digests for correlation; it covers `exc_info`/`stack_info` and is attached to uvicorn's own handlers as well as the app's | `core/redaction.py`, `core/logging.py`, `tests/security/test_redaction.py` |
| T18 | **PII in the audit trail** | `emit_audit` redacts `details` on the way in; the recorded details are non-PII context — classification, content type, size, purpose, method, field keys/ids, service slug, group/document/case/draft ids, event type and confirmation flags — never field values, never filenames, never document text | `audit/service.py`, `tests/integration/test_applications_api.py::test_audit_events_never_contain_draft_values` |
| T19 | **Aadhaar propagation** | Filtered from profile reads, promotions, draft snapshots, values, validation, export, packets and the `/fields` response; legacy rows deleted by migration | `core/privacy.py`, migration `b7e4f1a2c9d3`, PR #52 |
| T20 | **Unauthorised read of the stored bytes** | AES-GCM at rest; the key is held by the OS account, never beside the bytes it protects | `vault/storage.py`, `core/config.py`, `tests/security/test_storage_encryption.py` |

**Residual:** T20 has one application control, and it is not a boundary against
the OS account. Blobs are ciphertext, so a copied `.bin`, a stale backup of the
vault directory or an accidental read yields bytes without meaning; the key
sits on the same host under the same OS account, and the database stays
plaintext, so an attacker with the machine or that account has everything
(§6.1). T17 is content-blind: it recognises shapes, not meaning, so a
name, an address or a free-text note is not redacted, and a parser exception
message is covered only insofar as it contains an email or a digit run. T19
now leaves only a marker: the `aadhaar_number` value is stored as `[REDACTED]`,
so a database reader learns that the line existed and where, not what it said.
The number still survives in the document bytes, which is why A2 is listed as
re-derivable from A1 and why `data-map.md` §3.3 still calls the blob the edge.

### 5.5 Availability, integrity of records, and the insider

| ID | Threat | Control | Where |
|---|---|---|---|
| T21 | **One participant exhausting the budget** | Per-IP 1200/hour **and** per-session 200/hour, so a household or a CSC counter is not one bucket; upload 30/hour, content 100/hour, export 20/hour; the key is a digest, so tokens never reach a 429 log | `core/rate_limit.py`, `tests/integration/test_rate_limits.py`, `tests/unit/test_rate_limit_keys.py` |
| T22 | **Health probes exhausting the budget** | `/health` is exempt from the application limits | `core/rate_limit.py::EXEMPT_PATHS` |
| T23 | **Audit trail tampering or deletion** | None in the application: no append-only store, no hash chain, no external sink. A DB owner can edit rows | — |
| T24 | **Insider reads or exports everything** | None in the application: no admin panel, but no barrier either — the facilitator holds the database and the vault | — |
| T25 | **Loss of the laptop** | Blobs are ciphertext, but the key sits on the same disk and the database is plaintext; no backup | — |
| T26 | **Silent boundary change by a future contributor** | CI gate (`scripts/check.sh` on every push: ruff, pyright, pytest, eslint, tsc, vitest, production build), CodeQL on push and PR, a PR template that asks about portal bypasses, and this file plus the portal register as the place a boundary change must be recorded | `.github/workflows/ci.yml`, `.github/pull_request_template.md` |

**Residual:** T23–T25 are accepted for the synthetic pilot and are exactly why
real documents are out of scope. T21's counters live in process memory, so with
more than one worker the effective budget multiplies (readiness ledger item 9).

### 5.6 Deployment and supply chain

| ID | Threat | Control | Where |
|---|---|---|---|
| T27 | **Production misconfigured into a bypass** — dev sign-in on, insecure cookie, http WebAuthn origin, or `RINAVI_ENVIRONMENT` unset | Fail-closed settings validator: an unset environment is an error that names the variable, and production rejects dev sign-in, `cookie_secure=false` and a non-https WebAuthn origin. API docs and OpenAPI are not registered in production | `core/config.py::_reject_unsafe_production`, `main.py::create_app`, `tests/test_config.py` |
| T28 | **Clickjacking, MIME sniffing, referrer leakage, ambient device permissions** | `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` denying geolocation/microphone/camera, COOP `same-origin`, plus a matching `frame-ancestors 'none'` in the CSP; HSTS in production | `main.py::SECURITY_HEADERS`, `apps/web/next.config.ts`, `tests/security/test_security_headers.py` |
| T29 | **CORS opens credentials to an attacker origin** | Fixed allow-list from settings (`http://localhost:3000` by default); `allow_credentials` with an explicit origin list, never `*` | `core/config.py`, `main.py`, `tests/integration/test_cors.py` |
| T30 | **Compromised dependency or action** | CodeQL, Dependabot for pip/npm/actions, GitHub Actions pinned by major tag, `npm audit` reports **0** on `main` (dev and prod) | `.github/workflows/ci.yml`, `apps/web/package.json` |
| T31 | **Container runs as root or with writable app code** | Backend and web images run as UID 10001; migrations run from an entrypoint before uvicorn; every compose port binds loopback | `backend/Dockerfile`, `apps/web/Dockerfile`, `infra/compose/compose.yaml`, PR #65 |

**Residual:** base images float on channel tags (`python:3.14-slim`,
`node:24-slim`, `postgres:16`), so a rebuild can change the runtime without a
commit — a deliberate choice to keep patch flow, recorded in readiness "Track B
follow-ups" §4. `npm audit --omit=dev` is 0 on `main`; PR #70 adds the Playwright
test dependency, whose dev-only advisories do not affect the shipped bundle,
and the fix is a lockfile bump when patched.
Container **builds** are covered by the `docker` job added in PR #68, which runs
on any PR touching `backend/`, `apps/web/`, `infra/compose/` or the workflow
file. It passed on that PR and is now a required `protect-main` check.

## 6. Accepted risks (synthetic pilot only)

Each is accepted *because* every document is fake, and each names what reopens
it. These are not "we will get to it"; they are the reasons the pilot is
phase A rather than a launch.

| # | Risk | Why it is acceptable now | Reopens when |
|---|---|---|---|
| 6.1 | A plaintext database and a blob key held on the same host | SPECIMEN documents only; one machine. **Decided 2026-11-24 (D2):** accepted for the synthetic pilot against a pre-commitment that blobs are encrypted before the first real document — the whole file, not the extracted fields, because the Aadhaar number is inside the upload. **Landed 2026-11-25 (item 101, PR #110):** blobs are AES-GCM ciphertext and production refuses to start without a key, so what remains accepted is the database, which holds no Aadhaar digits, and the key's presence on the host | The first real document, storage leaving the founder's machine, a hosted or shared machine, or key custody moving off the host (D2, item 101) |
| 6.2 | No admin barrier against the facilitator | One facilitator, named in the notice, who already controls the machine | Any hosted or multi-operator deployment |
| 6.3 | Audit rows editable and permanent | They hold no content, and no incident process exists yet to need them as evidence | Real documents, or an incident-response requirement (item 85) |
| 6.4 | No backup, so deletion is also loss | Fake data, re-creatable by hand | Any real document, or a promised restore (item 85) |
| 6.5 | No retention or session sweep | Small volume, disclosed in the retention policy | Real documents (item 68) |
| 6.6 | Dev sign-in creates accounts for any email | Disabled by default, refused in production, and **D10 (decided 2026-11-25) takes it out of the pilot**: sessions run in an invite-only sign-in mode where the facilitator issues a single-use invite on the host and the participant never types an address. The mode is item 103, and runbook gate G4 refuses to start a session until it exists | Any environment where `RINAVI_DEV_SIGNIN_ENABLED=true` is reachable by a participant |
| 6.7 | An Aadhaar line is still recognised in `extracted_fields` (stored as `[REDACTED]`, never the digits) | The pilot's Aadhaar values are visibly fake, and no number is stored | Real documents (item 35 residual) |
| 6.8 | Parsing inside the upload request (thread-offloaded), single worker | One participant at a time, supervised | Concurrent users, or a job queue with a worker-level kill timeout (ledger item 1) |

## 7. What this model does not cover

- **Hosted deployment.** No host is chosen (readiness decision 7). A hosting
  provider becomes a processor, adds a network boundary at B1, and makes TLS,
  browser-session hardening, log retention and possibly a WAF in scope. This
  document must be rewritten, not amended, at that point.
- **The public static demo and the rest of `docs/`.** GitHub Pages publishes
  `docs/`, including a synthetic-only demo that stores data in the visitor's own
  browser and never calls the API or any server (`data-map.md` §10), alongside
  the handbook and these compliance documents. It shares no code path, no
  store and no credential with the pilot deployment, and it accepts no
  document bytes on any server, so it is outside this model. Reopens if the
  demo gains a server, an upload path, analytics or any link to the pilot's
  data, or if anything published under `docs/` starts carrying pilot data.
- **Real documents.** Blob encryption is in code (item 101); OCR, real scans, real
  Aadhaar numbers, key custody and rotation, and retention are post-gate.
- **The portal side.** What the citizen does in their own browser is outside the
  system; `portal-permission-register.md` records what RINAVI may do with a
  portal, which today is nothing.
- **The pilot folder.** Notes, recordings and screenshots live outside the
  system and are governed by `recording-consent.md`, not by any control here.
- **Mobile, accessibility and localisation.** Not modelled; the pilot is
  desktop, English and supervised.
- **Physical and insider coercion.** Not modelled; out of reach of a code
  review.

## 8. Review triggers

Reopen this model when any of the following changes — each one moves a boundary
rather than adding a feature:

1. A host, domain, TLS terminator or reverse proxy is added.
2. More than one backend worker or instance runs.
3. A real document, real Aadhaar number or real portal credential is accepted.
4. Key rotation, a KMS or HSM, object storage, OCR, email, analytics, error
   reporting or an AI API is introduced — each is a new processor or a new store.
5. A browser extension, portal adapter or any runtime call to a portal is
   proposed (also a register change: A1 → A2).
6. Authentication changes: a password, a recovery flow, a second factor, an
   admin or staff role.
7. A new module or route family is added — T1's residual lives here.
8. A dependency advisory affects shipped code, or a base image is re-pinned.

## 9. Version history

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-11-19 | First draft: 31 threats across six groups, eight accepted risks, review triggers tied to the readiness decisions |
| 0.2 | 2026-11-19 | Public copy redacted: residual paragraphs kept at risk-category level; exploit-level detail moved to the private review material; pending branch names replaced with PR numbers |
| 0.3 | 2026-11-23 | Scoped the public GitHub Pages demo and the rest of `docs/` out of §7; corrected risk 6.7, asset A2, the T19 residual and the handbook's Aadhaar passages, since the extracted Aadhaar value is now stored as `[REDACTED]` |
