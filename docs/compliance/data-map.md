# Data map — V1, synthetic pilot

**Status:** draft for the WP2 legal/privacy review. **Date:** 2026-11-19, against
`main` @ `45c63d7`. **Scope:** the single RINAVI deployment used for the phase A
pilot described in `pilot-plan.md`.
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
| Document bytes (blobs) | `<storage_dir>/<user_id>/<document_id>.bin`, default `backend/data/vault` | No |
| Session cookie | Browser, `rinavi_session`, HttpOnly, SameSite=Lax, 7-day TTL | TLS only (not yet deployed) |
| Rate-limit counters | In process memory (`memory://`), keyed by IP and session | N/A, ephemeral |
| Application logs | Process stdout/stderr, redaction filter applied | No |
| Pilot folder | Outside the system, on the facilitator's machine | No |

Encryption at rest is accepted-not-done for synthetic data only (readiness
ledger, item 2). Blobs are plaintext `.bin` files readable by the OS user that
runs the backend.

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
| `extracted_fields` | `field_key`, `value`, `confidence`, `locator` per document | Field values read from the document, **including `aadhaar_number` when present** | Cascade-deleted with the document |
| blob store | The uploaded bytes, unmodified | The whole document | Deleted before the row; account deletion purges the user's directory |

`extracted_fields` is the honest edge in this map: A1 (item 35) stops Aadhaar
from reaching a profile, draft, packet, export or the `/fields` response, but
the extracted value itself is still written to this table and still readable by
anyone with database access. Under the pilot that value is a fake SPECIMEN
number; with real documents this row would need a decision (drop on write, or
encrypt).

### 3.4 Profile

| Table | Holds | Personal data | Retention |
|---|---|---|---|
| `profile_values` | `field_key`, `value`, `status`, `source_document_id`, `source_locator`, `confidence`, `stale_reason`, `correction_history` (JSON), `created_at`, `updated_at` | The citizen's name, address, income, date of birth, gender, father's name | Until account deletion; no per-value delete route |

Deleting a source document sets `source_document_id` to NULL and marks the
value stale; it does not delete the value. There is no route that removes a
profile value — status is `confirmed`, `needs_review` or `rejected`, and a
rejected value still has its text stored.

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
| `audit_events` | `action`, `resource_type`, `resource_id`, `details` (JSON, redacted), `actor_user_id`, `created_at` | Pseudonymous: actor UUID and resource UUID; `details` carries classification, content type, size and purpose | Indefinite; **survives account deletion** with `actor_user_id` set to NULL |

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
| `profile.storage` | Every `/profile` route: read, promote, confirm, correct, reject | `profile_values`, reads `documents` to promote |
| `applications.preparation` | Every `/applications` route: drafts, values, links, validation, export, packet | `application_drafts`, reads `profile_values` and `documents` |
| `locker.tracking` | `/locker` routes: cases, events | `application_cases`, `case_events` |

Three review points, stated as questions rather than conclusions:

1. **Case creation under `locker.tracking`.** A case snapshots draft values and
   evidence. The route is gated on `locker.tracking` alone, so confirm the
   purpose labels are broad enough to cover reusing preparation data inside a
   tracked case.
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
   account. It is now ungated the same way (`fix/ungate-draft-deletion`, with
   tests for the withdrawn-consent path and for cross-account isolation);
   reading, editing, exporting and completing a draft stay behind the purpose.
   Profile values and cases still have no delete route at all (§8), so erasure
   coverage remains incomplete for them — that is the question left for the
   reviewer, not the gate.

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
  hosted yet (readiness decision 7).
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
| Blobs are plaintext on local disk | Anyone with the disk has the documents | Item 64, accepted for synthetic only |
| `extracted_fields` keeps Aadhaar when present | A hidden but stored identifier | Item 35 residual; pilot uses fake numbers |
| Export returns only `user` + `consent_records` | A citizen cannot take documents or profile values with them | Item 65, accepted for the pilot |
| No retention sweep, no session sweep, no audit sweep | Expired sessions and old audit rows accumulate | Item 68 |
| Cases have no delete route | A recorded case can only be removed by deleting the account | Part 6, accepted |
| No backup or restore drill | A disk failure loses everything; "deleted" also means gone | Item 85 |
| Log retention depends on the host | Undefined today | Decide with hosting |

## 9. What is deliberately not in the system

No Aadhaar number in profiles, drafts, packets or exports. No portal password
field, no OTP field, no CAPTCHA handling, no portal session, no cookies for any
government site. No location, contacts, device identifiers, advertising IDs or
behavioural analytics. No third-party SDK in the web app. No OCR service and no
inference API. See `pilot-plan.md` §6 for the operational form of this list.
