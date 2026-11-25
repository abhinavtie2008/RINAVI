# Reviewer brief — WP2 legal/privacy review

**To:** the qualified legal/privacy reviewer (not yet engaged) ·
**From:** the pilot owner · **Date:** 2026-11-23 · **Against:** `main` @ `a0732fb` (re-stamped at each re-cut)
**Amended:** 2026-11-24 — the Hindi comprehension layer added to the review scope (ADR-0006).
**Amended:** 2026-11-25 — an answer sheet added before the decision box: what a reply has to cover.

The reviewer's identity and engagement terms are held privately, not in this
repository; the note in `docs/compliance/README.md` records what is public and
what is not.

**The ask:** approve, approve with conditions, or decline the **phase A synthetic
pilot** described by the eight documents in this folder, plus the Hindi comprehension text below. They describe the system;
this page states what we need you to decide. Not legal advice.

**Scope.** Assist-only income-certificate assistant: nine backend modules, one
service pack, a Next.js PWA — RINAVI prepares, the citizen submits on the official
portal. Synthetic `SPECIMEN` documents only: no real Aadhaar, no portal
credentials, no mobile numbers. One machine, loopback ports, an unencrypted
database with encrypted document files, no host chosen, **no portal access at
all** (every register row is A0). Adult supervised
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

## The Hindi text — and a second signature

The pilot's own words are being prepared in Hindi as a **comprehension layer**
over the English record (ADR-0006): the consent purposes, a summary of the
notice, an explanation of the declaration, the validation messages that block
progress, and the official-channel guidance. The government's quoted text — the
form labels and the declaration itself — stays English, with the Hindi beside it
as an explanation, never as a substitute.

Two consequences for this review:

- The Hindi summary and the declaration explanation are **in scope** alongside
  the eight documents, so the engagement needs a **Hindi-fluent reviewer** — the
  same person if qualified, or a second reader. We will not put unreviewed
  translated legal text in front of a participant.
- Where the two versions differ, **English governs**, and the notice will say so
  once the Hindi text exists. The Hindi artefacts are added only after you
  approve them; the English pilot does not wait for them.
## Risks we ask you to see accepted — synthetic only

From `threat-model.md` §6; each is accepted *because* every document is fake, and
each names what reopens it.

| # | Risk | Reopens when |
|---|---|---|
| 6.1 | The database is plaintext and the blob key sits on the same host; the blobs themselves are AES-GCM (item 101) | First real document, or storage leaves the founder's machine |
| 6.2 | No admin barrier against the facilitator | Any hosted or multi-operator deployment |
| 6.3 | Audit rows editable and permanent | Real documents, or an incident-response requirement |
| 6.4 | No backup, so deletion is also loss | Any real document, or a promised restore |
| 6.5 | No retention or session sweep | Real documents (item 68) |
| 6.6 | Dev sign-in creates accounts for any email | Any environment where a participant can reach it. The pilot runs invite-only instead (D10, item 103), and no session starts before that mode exists |
| 6.7 | An Aadhaar line is still recognised, though the value is stored as `[REDACTED]` | Real documents (item 35 residual) |
| 6.8 | Parsing inside the upload request (thread-offloaded), single worker | Concurrent users, or a job queue with a worker-level timeout |

**Outside this review:** hosting, TLS, proxy, WAF; key custody, rotation and
backup; object storage; OCR and real scans; retention automation; DigiLocker; any extension or
portal adapter (A0 → A2, with its own security review); mobile, accessibility,
localisation; physical or insider coercion. Each reopens the threat model —
rewritten, not amended.

**Sign-off means** item 83 closes and the pilot may run as `pilot-plan.md`
describes. It brings no host, no real documents, no portal access, no Aadhaar
handling, no claim of government approval or faster processing.

## What we need back

Answer in whatever format suits you. This is the shape we can act on, and a
reply that covers 1–6 plus the box below closes item 83. One page is enough.

1. **You.** Name, capacity (advocate, firm, in-house counsel, DPO), and whether
   you have any current or former relationship with the Delhi Revenue
   Department, an e-District vendor or the portal operator. Whether you can
   review the Hindi layer yourself, or need a Hindi-fluent second reader.
2. **Q1–Q3.** For each: our reading, the other reading, or a third. A sentence
   of reasoning is enough; a citation is welcome, not required. One question
   from outside the eight documents: the discovery sessions (item 82) record
   interviews under `recording-consent.md` — may they reuse it unchanged, or
   does an interview need its own form?
3. **The eight risks.** For 6.1–6.8: accept, accept with a condition, or
   reject. Where a condition is code, say what it must do, not how.
4. **The portal items.** `portal-permission-register.md` §8 — six items, each a
   yes or no plus a line.
5. **The documents.** For `privacy-notice-draft.md`, `terms-draft.md`,
   `retention-policy.md`, `recording-consent.md`, `portal-permission-register.md`
   and `threat-model.md` §6: sufficient, sufficient with edits, or not
   sufficient — and which sentence. Then the five values only you can settle:
   entity name, address, contact email, grievance officer (name and email), and
   whether the retention periods stand as written.
6. **The decision.** The box below, your name, the date, and a reference we can
   quote in `data-map.md` §4 and `wp8-pilot-readiness.md`.

## Decision

- [ ] Approved for phase A (synthetic) as described
- [ ] Approved with conditions — below
- [ ] Declined

Answers to Q1–Q3 and any conditions are recorded in `data-map.md` §4 and
`wp8-pilot-readiness.md`; a change that moves a trust boundary reopens the threat
model.

Reviewer: ______________________  Date: __________  Reference: __________
