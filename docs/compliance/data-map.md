# Data map — V1, synthetic pilot

**Status:** draft for the WP2 legal/privacy review. **Date:** 2026-11-19, against
`main` @ `fee4e9f`. **Amended:** 2026-11-25 — blob encryption (item 101, PR #110),
against `main` @ `f541019`. **Scope:** the single RINAVI deployment used for the
phase A pilot described in `pilot-plan.md`.
**Authority:** `wp8-pilot-readiness.md` stays authoritative for compliance
decisions; this file records *where data actually lives*. Neither is legal
advice.

Verified against the code and Alembic migrations on that commit — table and
column names below are quoted from the schema, not from a diagram. Column lists
are abridged to the fields that matter for privacy; IDs, timestamps and
foreign keys are omitted except where they carry meaning.

## 1. Roles

| Role | Who | Notes |
|---|---|---|
| Data Fiduciary | The pilot owner (founder) | Determines purpose and means; named in the privacy notice |
| Data Principal | Pilot participant | Adult volunteer; see `pilot-plan.md` §3 |
| Data Processor | **None** | No vendor processes personal data on RINAVI's behalf today: no analytics, no error reporting, no email/SMS provider, no AI inference, no object storage, no managed database |
| Sub-processor | **None** | Follows from the above |

There is no Data Processing Agreement in force because there is no processor.
That changes the moment hosting, email, analytics or an LLM is added; each of
those is a new processor and must be recorded here first.

## 2. Where the data lives

| Store | Path / mechanism | Encrypted at rest |
|---|---|---|
| Application database | SQLite file in dev and test; PostgreSQL 16 in the compose demo | No |
| Document bytes (blobs) | `<storage_dir>/<user_id>/<document_id>.bin`, default `backend/data/vault` | Only when a key is configured — AES-GCM (item 101); the compose demo sets none |
| Session cookie | Browser, `rinavi_session`, HttpOnly, SameSite=Lax, 7-day TTL | TLS only (not yet deployed) |
| Rate-limit counters | In process memory (`memory://`), keyed by IP and session | N/A, ephemeral |
| Application logs | Process stdout/stderr, redaction filter applied | No |
| Pilot folder | Outside the system, on the facilitator's machine | No |

Every store except the blobs is plaintext, and a blob is ciphertext only when a
key is configured: AES-GCM with a fresh nonce and the user/document ids bound
in, and a production configuration refuses to start without a key (item 101). The key sits
on the host, so this defeats a stray copy of a `.bin` file or an accidental read,
not someone who takes the whole machine — and the database, with the values
parsed out of those documents, is still plaintext.

## 3. Tables

### 3.1 Identity

| Table | Holds | Personal data | Retention |
|---|---|---|---|
| `users` | `email` (320), `display_name` (120), `created_at` | Email identifies the person; display name is self-declared | Until account deletion; deleted with the row |
| `sessions` | `token_hash` (SHA-256 of the cookie token), `created_at`, `expires_at`, `revoked_at` | Pseudonymous; links to `user_id` | Rejected after `expires_at` (7 days); rows are not swept yet |
| `credentials` | `credential_id`, `public_key`, `sign_count` | Passkey public key only; no private key ever reaches the server | Until account deletion |

The cookie's value is never stored — only its SHA-256. A leaked database does
not yield a usable session token.

### 3.2 Consent

| Table | Holds | Personal data | Retention |
|---|---|---|---|
| `consent_records` | `purpose`, `policy_version` (currently `1.0`), `granted_at`, `withdrawn_at` | Consent history tied to `user_id` | Until account deletion; withdrawal sets `withdrawn_at`, it does not delete the row |

Rows are append-only in practice: withdrawing sets `withdrawn_at`, and a later
re-grant adds a new row after withdrawing the active one. The history is the
proof of what was consented to when.

### 3.3 Documents

| Table | Holds | Personal data | Retention |
|---|---|---|---|
| `documents` | `original_filename` (255), `content_type`, `size_bytes`, `status`, `classification`, `note`, `created_at`, `processed_at` | The filename can contain a name and a document type | Until the document is deleted or the account is deleted |
| `extracted_fields` | `field_key`, `value`, `confidence`, `locator` per document | Field values read from the document; an `aadhaar_number` line is stored as the literal marker `[REDACTED]`, not the digits | Cascade-deleted with the document |
| blob store | The uploaded bytes, unmodified | The whole document | Deleted before the row; account deletion purges the user's directory |

A1 (item 35) stops Aadhaar from reaching a profile, draft, packet, export or
the `/fields` response, and `documents/pipeline.py` stops it reaching this
table: the line is still recognised, so the document classifies as identity,
but what is written is the literal marker `[REDACTED]`. A reader with database
access learns that a document carried an Aadhaar line, not what the number was.
What remains is structural — `field_key`, `confidence` and `locator` say where
in the document the line was — and the number itself still sits in the document
bytes (§3.2, asset A1) until the document is deleted. Real documents still need
the encryption-at-rest decision; the extracted-value half of that gap is closed.

### 3.4 Profile

| Table | Holds | Personal data | Retention |
|---|---|---|---|
| `profile_values` | `field_key`, `value`, `status`, `source_document_id`, `source_locator`, `confidence`, `stale_reason`, `correction_history` (JSON), `created_at`, `updated_at` | The citizen's name, address, income, date of birth, gender, father's name | Until account deletion; a non-confirmed value can be rejected (hard-deleted), a confirmed value has no delete route |

Deleting a source document sets `source_document_id` to NULL and marks the
value `stale`; it does not delete the value. The statuses are `unconfirmed`,
`confirmed` and `stale`. `POST /profile/values/{id}/reject` hard-deletes a
value unless it is `confirmed`, and is deliberately not consent-gated, so a
participant can reject a value extracted under a purpose they have withdrawn.
A `confirmed` value has no per-value delete route of its own; deleting its
source document marks it `stale` (after which reject removes it), and account
deletion removes it regardless.

A correction makes the value the citizen's own rather than the document's:
`POST /profile/values/{id}/correct` clears `source_document_id`,
`source_locator` and `confidence`, records the old value in
`correction_history`, and clears `stale_reason`. A corrected value therefore
survives deletion of the document it was read from, and it is the only profile
value with no provenance pointer — by design, because the citizen is now the
source. The cost is recorded rather than hidden: the pointer to the document a
corrected value was read from is not kept — `correction_history` holds the old
value and the time, and the `profile.value_corrected` audit event holds the
field key, so the link back to the source document is gone by design.

### 3.5 Preparation and tracking

| Table | Holds | Personal data | Retention |
|---|---|---|---|
| `application_drafts` | `service_slug`, `service_name`, `pack_version`, `template_snapshot`, `values` (JSON), `document_links` (JSON), `declaration_confirmed`, timestamps | Field values copied into the draft; links to document IDs | Until the draft is deleted or the account is deleted |
| `application_cases` | `service_slug`, `pack_version`, `packet_snapshot` (JSON), `packet_text` (text), `status`, `reference_number`, `acknowledgement_number`, `deadline_at`, `outcome_notes`, timestamps | A frozen copy of the packet text plus any portal reference number the citizen records | Until account deletion; **no delete route exists** |
| `case_events` | `type`, `payload` (JSON), `created_at` | Portal reference numbers and outcome notes | Cascade-deleted with the case |

`application_cases.packet_text` is the largest concentration of personal data
in a single column: it is the assembled application text, including the values
and the evidence list. It is written when the citizen records a case, and it
does not shrink afterwards — editing the draft does not rewrite a case.

### 3.6 Audit

| Table | Holds | Personal data | Retention |
|---|---|---|---|
| `audit_events` | `action`, `resource_type`, `resource_id`, `details` (JSON, redacted), `actor_user_id`, `created_at` | Pseudonymous: actor UUID and resource UUID; `details` carries non-PII context — classification, content type, size, purpose and method, plus field keys/ids, service slug, group/document/case/draft ids, event type and confirmation flags; an email on `account.deleted` is redacted before storage | Indefinite; **survives account deletion** with `actor_user_id` set to NULL |

Actions recorded: `identity.signed_in`, `identity.signed_out`,
`identity.passkey_registered`, `consent.granted`, `consent.withdrawn`,
`document.uploaded`, `document.processed`, `document.deleted`,
`profile.values_promoted`, `profile.value_confirmed`, `profile.value_corrected`,
`profile.value_rejected`, `application.draft_created`,
`application.draft_refreshed`, `application.draft_deleted`,
`application.draft_exported`, `application.draft_field_updated`,
`application.document_linked`, `application.document_unlinked`,
`application.declaration_updated`, `application.case_created`,
`locker.event_recorded`, `locker.apply_again`, `account.deleted`.

Document content, field values and PII never reach `details`; the redaction
tests (`tests/security/test_redaction.py`) cover email addresses and 12-digit
runs. Audit rows are deliberately kept after erasure — they are the security
record — and the `ON DELETE SET NULL` on `actor_user_id` is what anonymises
them.

## 4. What each purpose covers

The four purposes are enforced as route dependencies, not as filters on the
data — a table can be touched under more than one purpose.

| Purpose | Gates | Data read or written |
|---|---|---|
| `documents.processing` | `/vault`: upload, list, get, content, fields, retry | `documents`, `extracted_fields`, blob store |
| `profile.storage` | Every `/profile` route except reject: read, promote, confirm, correct. Reject is deliberately ungated so erasure survives withdrawal | `profile_values`, reads `documents` to promote |
| `applications.preparation` | Every `/applications` route except the two draft-erasure routes (`DELETE /drafts/{id}` and `DELETE /drafts`): drafts, values, links, validation, export, packet | `application_drafts`, reads `profile_values` and `documents` |
| `locker.tracking` | `/locker` routes: cases, events | `application_cases`, `case_events` |

Three review points, stated as questions rather than conclusions:

1. **Case creation under `applications.preparation`.** The route
   `POST /applications/drafts/{id}/complete` snapshots draft values and
   evidence and writes `application_cases` + `case_events`; it is gated on
   `applications.preparation` alone. `POST /locker/cases/{id}/apply-again`
   requires both `locker.tracking` and `applications.preparation`. Confirm that
   preparing a packet under `applications.preparation` covers the case
   snapshot, or whether completion should also require `locker.tracking`.
2. **Promotion under `profile.storage`.** Promoting a document into the profile
   reads document fields, but the promote route is gated on `profile.storage`;
   the citizen will normally hold `documents.processing` already, and the review
   should confirm one purpose is enough.
3. **Deletion is gated inconsistently — resolved for drafts.**
   `DELETE /vault/documents/{id}` and `DELETE /auth/account` carry **no**
   consent dependency, and that is the right default: erasure must never be
   conditional on a grant the citizen may have just withdrawn.
   `DELETE /applications/drafts/{id}` was the exception — gated on
   `applications.preparation`, so a citizen who withdrew that purpose could
   delete a document but could only remove a draft by deleting the whole
   account. It is now ungated the same way (PR #71, with tests for the
   withdrawn-consent path and for cross-account isolation); reading, editing,
   exporting and completing a draft stay behind the purpose.
   The web app reaches erasure from the consent gate through the collection
   route `DELETE /applications/drafts` (PR #72), because the draft list itself
   returns 403 in that state — a bulk erase was chosen over a metadata listing
   so that erasure introduces no read of data whose purpose has been withdrawn.
   Cases still have no delete route at all (§8), and confirmed profile values
   only go with the account; non-confirmed values can be rejected. Erasure
   coverage therefore remains incomplete for cases and confirmed profile
   values — that is the question left for the reviewer, not the gate.

## 5. Flows

```
sign-in (dev or passkey)
  └─ users, sessions, credentials, audit(identity.*)
consent grant
  └─ consent_records, audit(consent.granted)
upload
  └─ blob store, documents, audit(document.uploaded)
parse
  └─ extracted_fields, documents.status, audit(document.processed)
promote
  └─ profile_values, audit(profile.values_promoted)
draft
  └─ application_drafts, audit(application.*)
record a case
  └─ application_cases, case_events, audit(application.case_created)
export / packet
  └─ nothing written; audit(application.draft_exported)
delete
  └─ blob, then rows; audit(document.deleted or account.deleted)
```

Nothing leaves the deployment. There is no outbound HTTP client for user data:
no email, no webhook, no portal call. Submission is manual, on the official
portal, by the citizen.

## 6. Who can see it

| Actor | Access |
|---|---|
| The citizen | Own rows only; every query is scoped by `user_id` from the session, never from a request parameter |
| The pilot facilitator | Whatever database and vault access the host gives the OS account running the backend; there is no admin panel |
| Other participants | Nothing: cross-account access is covered by tests (`test_documents_api.py`, `test_locker_api.py`) |
| The public | Nothing; no share links, no public profile |

## 7. Transfers, hosting and retention

- **Storage location:** the facilitator's machine for the pilot; nothing is
  hosted yet (readiness decision 7). The one hosted artifact is the static demo
  site in §10, which holds no pilot data.
- **Cross-border transfer:** none today. Host selection is unrecorded, so this
  section must be rewritten before any host is chosen.
- **Retention:** per-table above; the policy and its gaps are in
  `retention-policy.md`.
- **Deletion:** immediate and hard — no soft delete, no tombstone. Blobs are
  erased before the row that names them.

## 8. Gaps this map exposes

Each is already owned by a checklist item or recorded decision; none is a
surprise found here for the first time.

| Gap | Effect | Owner |
|---|---|---|
| The database is plaintext on local disk; blobs are ciphertext with the key on the same host | Anyone with the disk has the profile, drafts and parsed values; a whole-machine compromise gets the key too | Item 64 residual, accepted for synthetic only |
| An Aadhaar line is still recognisable, and the number is still in the blob | The fact and the location of the line survive; the digits survive in the uploaded bytes | Item 35 residual; the extracted value itself is `[REDACTED]` |
| Export returns only `user` + `consent_records` | A citizen cannot take documents or profile values with them | Item 65, accepted for the pilot |
| No retention sweep, no session sweep, no audit sweep | Expired sessions and old audit rows accumulate | Item 68 |
| Cases have no delete route | A recorded case can only be removed by deleting the account | Part 6, accepted |
| No backup or restore drill | A disk failure loses everything; "deleted" also means gone | Item 85 |
| Log retention depends on the host | Undefined today | Decide with hosting |
| `consent_records.purpose` is not constrained in the database | A direct write can store a purpose this map does not describe; the API refuses anything outside the four with 422, so the allow-list is an API guarantee, not a schema one | #118 (open), PR #117 |

## 9. What is deliberately not in the system

No Aadhaar number in profiles, drafts, packets or exports. No portal password
field, no OTP field, no CAPTCHA handling, no portal session, no cookies for any
government site. No location, contacts, device identifiers, advertising IDs or
behavioural analytics. No third-party SDK in the web app. No OCR service and no
inference API. See `pilot-plan.md` §6 for the operational form of this list.

## 10. Public demo site (static, GitHub Pages)

The `docs/` folder also holds a static demo of the web UI (`docs/index.html`,
`docs/assets/`), published with GitHub Pages. It is **not** the pilot
deployment, and §2–§9 do not describe it. It is recorded here because a public
URL is a surface a reviewer will ask about.

| Question | Answer |
|---|---|
| What does it store? | Whatever a visitor adds, in that visitor's own browser: `localStorage` key `rinavi.demo.v1` and `sessionStorage` keys `rinavi:suggested-links:*`. Nothing is sent to a server; the demo code contains no `fetch`, `XMLHttpRequest` or `sendBeacon`. |
| Who controls it? | The visitor. The account page exports the demo's records and metadata as JSON (document text is deliberately left out and stays in the browser) and can erase everything. |
| What data is meant to go in? | Synthetic only. The landing page, footer, trust page and vault say so, and the vault offers three made-up sample documents. |
| Third-party requests? | None. The two typefaces are bundled in `docs/assets/fonts/` under the SIL OFL 1.1, and there are no analytics, cookies or external scripts. |
| What does the host see? | GitHub, as the host, receives ordinary request metadata (IP address, user agent, path) for each visit, as any web host does. RINAVI has no say in those logs and has not treated this as a processor relationship because no pilot data is involved; the reviewer may see it differently. |
| Aadhaar? | An Aadhaar line in an uploaded text file is replaced with `[not kept by RINAVI]` before anything is stored or shown. |
| Where does it differ from the backend? | It reads `.txt` only; sign-in is a display name, not a passkey. Completing a draft needs `applications.preparation` alone, as the API does (§4, question 1), and opening the resulting case then asks for `locker.tracking`. |
| What else does the published site serve? | GitHub Pages publishes the whole `docs/` folder, not only the demo: the handbook and the documents in `docs/compliance/` and `docs/planning/` are public at the same origin. None of them contains pilot data, but publication of anything under `docs/` is publication to the internet, and dated snapshots should say so on their face. |
| What is it? | **An illustration, not a twin.** It shows the citizen journey and must keep the promises the trust page makes; everything else about it may differ from the app. The contract is five promises, quoted from that page: consent is off until granted and withdrawable at any time; a value you corrected yourself is kept when its source document is deleted (an untouched one is marked for a re-check); erasure works after withdrawal; the activity log is redacted; Aadhaar never enters profile, draft, packet or log. A behaviour outside those five is not promised and is not guarded. |
| How is it kept in step with the code? | `scripts/check_demo_sync.mjs`, run by `scripts/check.sh` and by CI, compares the demo's service pack and extraction rules with `catalog/` and `extraction.py`, and runs the same fixtures through both extractors. **It does not yet check the five trust-page promises** — that guard extension is requested from YooExE; until it lands, a regression on one of them reaches the public site silently, which is what #85 was (corrected values were dropped when their source document was deleted). Recording the gap here is deliberate: the demo's consent, provenance, erasure, audit and Aadhaar logic are in `docs/assets/js/core.js`, and nothing currently runs it. |
