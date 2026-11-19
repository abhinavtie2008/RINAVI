# Reviewer brief — WP2 legal/privacy review

**To:** the qualified legal/privacy reviewer named in `wp8-pilot-readiness.md`
**From:** the pilot owner · **Date:** 2026-11-19 · **Version:** 1, against `main` @ `ac8aa27`

**The ask:** approve, approve with conditions, or decline the **phase A synthetic
pilot** described by the eight documents in this folder. Those documents describe
the system; this page states what we are asking you to decide, and what we are
*not* asking. Nothing here is legal advice, and none of it clears the gate by
itself.

## 1. What you are reviewing

| | |
|---|---|
| System | Nine backend modules, one service pack (e-District income certificate), a Next.js PWA. **Assist-only:** RINAVI prepares; the citizen submits on the official portal |
| Data | Synthetic `SPECIMEN` documents only. No real Aadhaar, no portal credentials, no mobile numbers, no real scans |
| Deployment | One machine, loopback ports, plaintext disk, **no host chosen** (readiness decision 7) |
| Portal access | **None.** Every portal in the register is A0 — read by the citizen, never by RINAVI |
| Participants | Adult volunteers, supervised, one at a time, recorded only with separate consent (`recording-consent.md`) |
| Never | No submission, no OTP or CAPTCHA handling, no portal call, no outbound transfer of user data, no government affiliation claimed |

## 2. Three questions we cannot answer from inside the repository

These are open questions, not conclusions. Each names the route that creates the
issue, so the answer can be checked against the code. (The permission register
puts six further questions to you in its §8; those concern portal terms, naming
and quoting, not consent scope, and are not repeated here.)

**Q1 — Does completing a case belong under `applications.preparation` alone?**
`POST /applications/drafts/{id}/complete` snapshots the draft's values and
evidence into `application_cases` + `case_events`, and is gated on
`applications.preparation` only. Recording a case is otherwise a `locker.tracking`
activity — the citizen's own "apply again" path
(`POST /locker/cases/{id}/apply-again`) requires *both* purposes. Our reading is
that the snapshot is preparation, so one purpose suffices; the risk of the other
reading is that case history is written under a purpose the citizen may think
covers only drafts. **If you say completion needs both**, the change is one
dependency in `backend/app/modules/applications/routes.py` plus a test.

**Q2 — Is `profile.storage` enough to promote a document into the profile?**
The promote route reads `documents` and writes `profile_values`, but is gated on
`profile.storage` alone. The citizen will normally hold `documents.processing`
already, since that is how the document arrived. Our reading is that one
purpose is enough because promotion is a profile write; the alternative reading
would require both, which changes the consent prompt a participant sees.

**Q3 — Is our erasure coverage acceptable for phase A?**
Deletion is deliberately never gated on consent: `DELETE /vault/documents/{id}`,
`DELETE /auth/account`, and since #71 both draft-erasure routes are ungated, so a
citizen who withdraws a purpose can still erase. Two gaps remain and we are not
proposing to close them before the pilot: **cases have no delete route at all**,
and **confirmed profile values leave only with the account** (non-confirmed
values can be rejected). Both are recorded in `data-map.md` §4 and §8. The
question is whether that is acceptable while every document is fake, or whether
it must be closed first.

## 3. Risks we are asking you to see accepted — synthetic only

From `threat-model.md` §6. Each is accepted *because* every document is fake, and
each names what reopens it.

| # | Risk | Reopens when |
|---|---|---|
| 6.1 | Plaintext storage, no encryption at rest | First real document, or storage leaves the founder's machine |
| 6.2 | No admin barrier against the facilitator | Any hosted or multi-operator deployment |
| 6.3 | Audit rows are editable and permanent | Real documents, or an incident-response requirement |
| 6.4 | No backup, so deletion is also loss | Any real document, or a promised restore |
| 6.5 | No retention or session sweep | Real documents (checklist item 68) |
| 6.6 | Dev sign-in creates accounts for any email | Any environment where it is reachable by a participant |
| 6.7 | Aadhaar survives in `extracted_fields` | Real documents (item 35 residual) |
| 6.8 | Inline synchronous parsing, single worker | Concurrent users, or an async worker |

## 4. Outside this review

Hosting, TLS, reverse proxy and WAF; encryption at rest and object storage; OCR
and real scans; retention automation; DigiLocker; any browser extension or
portal adapter (which would move a register row from A0 to A2 and needs its own
security review); mobile, accessibility and localisation; physical and insider
coercion. Each of those **reopens the threat model** — rewritten, not amended —
rather than extending this brief.

## 5. What a sign-off changes, and what it does not

**Changes:** checklist item 83 closes; the WP2 gate stops being the blocker on
the repo side; the pilot may run as described in `pilot-plan.md`.
**Does not change:** no host, no real documents, no portal access, no Aadhaar
handling, no claim of government approval or faster processing. Those stay
blocked on their own decisions above.

## 6. Decision

- [ ] Approved for phase A (synthetic) as described
- [ ] Approved with conditions — listed below
- [ ] Declined

Answers to Q1–Q3, and any conditions, are recorded in `data-map.md` §4 and in
`wp8-pilot-readiness.md`; a change to any answer reopens the threat model only if
it moves a trust boundary.

Reviewer: ______________________  Date: __________  Reference: __________
