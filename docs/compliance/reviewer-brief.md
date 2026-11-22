# Reviewer brief — WP2 legal/privacy review

**To:** the qualified legal/privacy reviewer engaged by the pilot owner ·
**From:** the pilot owner · **Date:** 2026-11-19 · **Against:** `main` @ `ac8aa27`

The reviewer's identity and engagement terms are held privately, not in this
repository; the note in `docs/compliance/README.md` records what is public and
what is not.

**The ask:** approve, approve with conditions, or decline the **phase A synthetic
pilot** described by the eight documents in this folder. They describe the system;
this page states what we need you to decide. Not legal advice.

**Scope.** Assist-only income-certificate assistant: nine backend modules, one
service pack, a Next.js PWA — RINAVI prepares, the citizen submits on the official
portal. Synthetic `SPECIMEN` documents only: no real Aadhaar, no portal
credentials, no mobile numbers. One machine, loopback ports, plaintext disk, no host
chosen, **no portal access at all** (every register row is A0). Adult supervised
volunteers, one at a time, recorded only under separate consent. Never: submission,
OTP or CAPTCHA handling, portal calls, outbound transfer of user data, or any claim
of government affiliation. A static, synthetic-only demo of the web UI is also
published from `docs/` on GitHub Pages; it stores nothing outside the visitor's own
browser (`data-map.md` §10).

## Three questions we cannot answer from inside the repository

Each names the route, so an answer can be checked against the code. (The register's
§8 puts six further questions to you on portal terms and naming — not consent
scope, so not repeated here.)

**Q1 — Does completing a case belong under `applications.preparation` alone?**
`POST /applications/drafts/{id}/complete` snapshots draft values and evidence into
`application_cases` + `case_events`, gated on `applications.preparation` only —
while the citizen's "apply again" path requires both purposes. We read the
snapshot as preparation, so one purpose suffices; the other reading is that case
history is written under a purpose the citizen may think covers only drafts. *If
completion needs both:* one dependency in
`backend/app/modules/applications/routes.py` plus a test.

**Q2 — Is `profile.storage` enough to promote a document into the profile?**
The promote route reads `documents` and writes `profile_values`, gated on
`profile.storage` alone; the citizen normally holds `documents.processing` already,
since that is how the document arrived. We read promotion as a profile write, so
one purpose suffices; requiring both changes the consent prompt participants see.

**Q3 — Is our erasure coverage acceptable for phase A?**
Deletion is never gated on consent: `DELETE /vault/documents/{id}`,
`DELETE /auth/account` and (since #71) both draft-erasure routes are ungated, so a
citizen who withdraws a purpose can still erase, and the web app reaches it from
the consent gate without reading withdrawn data. Two gaps remain: **cases have no
delete route at all**, and **confirmed profile values leave only with the account**
(non-confirmed values can be rejected) — see `data-map.md` §4, §8. Must they close
before the pilot, or are they acceptable while every document is fake?

## Risks we ask you to see accepted — synthetic only

From `threat-model.md` §6; each is accepted *because* every document is fake, and
each names what reopens it.

| # | Risk | Reopens when |
|---|---|---|
| 6.1 | Plaintext storage, no encryption at rest | First real document, or storage leaves the founder's machine |
| 6.2 | No admin barrier against the facilitator | Any hosted or multi-operator deployment |
| 6.3 | Audit rows editable and permanent | Real documents, or an incident-response requirement |
| 6.4 | No backup, so deletion is also loss | Any real document, or a promised restore |
| 6.5 | No retention or session sweep | Real documents (item 68) |
| 6.6 | Dev sign-in creates accounts for any email | Any environment where a participant can reach it |
| 6.7 | Aadhaar survives in `extracted_fields` | Real documents (item 35 residual) |
| 6.8 | Parsing inside the upload request (thread-offloaded), single worker | Concurrent users, or a job queue with a worker-level timeout |

**Outside this review:** hosting, TLS, proxy, WAF; encryption at rest; object
storage; OCR and real scans; retention automation; DigiLocker; any extension or
portal adapter (A0 → A2, with its own security review); mobile, accessibility,
localisation; physical or insider coercion. Each reopens the threat model —
rewritten, not amended.

**Sign-off means** item 83 closes and the pilot may run as `pilot-plan.md`
describes. It brings no host, no real documents, no portal access, no Aadhaar
handling, no claim of government approval or faster processing.

## Decision

- [ ] Approved for phase A (synthetic) as described
- [ ] Approved with conditions — below
- [ ] Declined

Answers to Q1–Q3 and any conditions are recorded in `data-map.md` §4 and
`wp8-pilot-readiness.md`; a change that moves a trust boundary reopens the threat
model.

Reviewer: ______________________  Date: __________  Reference: __________
