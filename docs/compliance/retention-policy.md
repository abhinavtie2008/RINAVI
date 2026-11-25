# Retention policy — draft

**Status:** draft for the WP2 legal/privacy review. **Date:** 2026-11-19,
against `main` @ `fee4e9f`.
**Companion to:** `data-map.md` (where the data is), `privacy-notice-draft.md`
(what participants are told). Not legal advice.

## 1. Principle

Keep personal data only while it serves the purpose it was collected for, and
delete it when the citizen says so. In V1 that principle is met by **immediate,
hard deletion on request**, not by a background schedule. There is no soft
delete, no tombstone and no "deleted" flag. A document delete erases the file
first and commits the row deletion afterwards; the two stores are not one
transaction. A failed unlink returns 503 and keeps both, so the citizen can
retry; a crash between the unlink and the commit can leave a row whose file is
gone, which the API reports as `content_unavailable`.

This is deliberately the simplest thing that is honest. The consequence is that
there is also **no automatic expiry** for anything the citizen does not
explicitly delete, and no sweep that catches leftovers. Those gaps are listed in
§5 with their owners.

## 2. Retention by store

| Store | What it holds | Retention | How it ends |
|---|---|---|---|
| `users` | Email, display name | Until account deletion | `DELETE /auth/account` deletes the row |
| `sessions` | Session token hash, expiry | 7 days from issue (`session_ttl_hours = 168`) | Rejected after `expires_at`; sign-out sets `revoked_at`; rows removed with the account |
| `credentials` | Passkey public key, sign counter | Until account deletion | Cascade with the user |
| `consent_records` | Purpose, policy version, granted/withdrawn timestamps | Until account deletion | Cascade with the user; withdrawal sets `withdrawn_at` and keeps the row as proof |
| `documents` | Filename, type, size, status, classification | Until the document or the account is deleted | `DELETE /vault/documents/{id}`; cascade with the user |
| document blob | The uploaded bytes, as AES-GCM ciphertext while a key is configured | Same as its `documents` row | File removed **before** the row; a failed unlink returns 503 and keeps both, so the citizen can retry |
| `extracted_fields` | Field values read from a document | Same as the document | Cascade on document delete |
| `profile_values` | Name, address, income, date of birth, gender, father's name | Until the account is deleted; a non-confirmed value can be rejected | Cascade with the user; `POST /profile/values/{id}/reject` hard-deletes a non-confirmed value without a consent check; a confirmed value has no per-value delete route (deleting its source document makes it `stale`, and reject then removes it) |
| `application_drafts` | Draft values, evidence links, declaration flag | Until the draft or the account is deleted | `DELETE /applications/drafts/{id}`, or `DELETE /applications/drafts` for all of them; both are ungated, so they also work after `applications.preparation` is withdrawn; cascade with the user |
| `application_cases` | Packet snapshot and text, reference numbers, outcome notes | Until account deletion | **No delete route**; cascade with the user |
| `case_events` | Case timeline entries | Same as the case | Cascade on case delete (account deletion today) |
| `audit_events` | Action, resource id, redacted details | Kept as the security record; no expiry | Survives account deletion; `actor_user_id` becomes NULL |
| rate-limit counters | IP and session keys | Minutes (sliding window) | In-process memory; lost on restart |
| logs | Request lines and errors | Host-dependent, undefined | Decided with hosting |
| pilot folder (notes, recordings) | Interview material | 90 days after the session, or at pilot close if sooner | Manual deletion by the facilitator, recorded in the folder index |

## 3. Deletion mechanics

**Document deletion.** The route reads the row, erases the blob, then deletes
the row. If the erase fails, the request returns 503 and nothing is deleted —
retrying is the recovery path. Profile values sourced from that document stay,
marked stale, because the citizen may have corrected them by hand.

**Account deletion.** The route purges `<storage_dir>/<user_id>/` first and
returns 503 if that fails, then deletes the user row. Every table with a
`user_id` or `document_id` foreign key cascades: sessions, credentials, consent
records, documents, extracted fields, profile values, drafts, cases and case
events. The response also clears the session cookie, and an `account.deleted`
audit event is written.

**What survives an account deletion, and why.** Only `audit_events`, with the
actor link severed. Its `details` never contains document content, field values
or PII — only classification, content type, size, purpose and method — and
resource identifiers are UUIDs that no longer resolve to a row. This is a
deliberate choice: without it there is no evidence of how the system was used,
and no way to investigate an incident.

**Bulk deletion outside the app.** If the facilitator must wipe everything — for
example at the end of the pilot — the sequence is: stop the app, delete the
vault directory, **delete the key file**, drop and recreate the database.
Deleting the database is the only way to clear audit rows, and deleting the key
is what makes any ciphertext left behind unreadable: ciphertext whose key
survives is not erased. There is no script for this yet, and it is a real gap
for the pilot close-out (§5).

## 4. Sessions and revocation

- Session TTL is 7 days. An expired session is rejected on read, so it cannot
  authenticate anyone after `expires_at`.
- Sign-out revokes the row and clears the cookie.
- Expired and revoked rows accumulate until the account is deleted, because no
  sweep removes them. Each row is a SHA-256 hash and two timestamps, so the
  volume is small; the privacy exposure is minimal, but the rows are still
  personal data linked to a user id.

## 5. Gaps, owners and reopen triggers

| Gap | Consequence | Owner |
|---|---|---|
| No retention scheduler | Expired sessions, old audit rows and any orphaned blob stay forever | Item 68 (readiness ledger item 6) |
| A failed delete keeps file and row together | Nothing is orphaned, but nothing is reclaimed either, until someone retries | Accepted; documented behaviour, 503 + retry |
| No delete route for cases or confirmed profile values | Cases and confirmed values only go with the account; non-confirmed values can be rejected | Part 6; accepted for the pilot |
| No pilot-wide wipe script | Close-out depends on manual steps in the right order | Pilot operations, to be written before the first session |
| Audit rows never expire | Grows without bound; must not become a shadow profile | Item 68 when real documents are in scope |
| Log retention undefined | Depends on the host chosen | Decide with hosting (item 58) |
| No backup, so no restore | "Deleted" is final; a disk failure is total loss | Item 85 (backup/restore drill) |
| The blob key is stored once, on the same host | Losing it makes every stored document unreadable; it is also what makes a wipe complete | Gate G7 (backup/restore), runbook §6 |

None of these is acceptable once real documents are accepted. All of them are
acceptable for fake documents on one laptop, provided participants are told —
which the privacy notice does, in §7 and §9.

## 6. Pilot close-out

At the end of phase A:

1. Tell every participant the deletion date, in writing, before it happens.
2. Delete every pilot account through the app (so blobs and cascades run the
   tested path).
3. Delete the vault directory, delete the storage key file (so leftover
   ciphertext cannot be read), drop the database, then recreate it empty.
4. Delete the pilot folder (notes, recordings, screenshots) and record the
   deletion in `docs/evaluation/` **without personal data**.
5. Record the completion date in the pilot log.

Step 3 is the only way to remove audit rows, and step 4 is outside the system
entirely — which is why the recording consent form states the same date.

## 7. Review

Review this policy when any of the following changes: hosting, key custody or
rotation, OCR, async workers, export completeness, the second service pack, or
the first real document. Each of those adds a store or a processor, and each must
land with its retention answer, not after it.
