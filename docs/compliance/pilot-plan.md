# Pilot plan — phase A (synthetic, controlled)

**Status:** draft for the WP2 legal/privacy review. **Date:** 2026-11-18, against `main` @ `fee4e9f`.
**Authority:** `docs/compliance/wp8-pilot-readiness.md` stays authoritative for compliance decisions; this file records *how the first pilot runs*. Neither is legal advice.

## 1. What this pilot is

A supervised usability and trust study: **10–20 real people** work through the
Delhi income-certificate flow in RINAVI over **2–3 weeks**, using a scripted
persona and **SPECIMEN documents**. It is not a service launch, and no real
citizen document, real Aadhaar number or portal credential is accepted.

The participants are real; the paperwork is not. That is a deliberate limit, not
an oversight — see §2.

## 2. Why the pilot is synthetic (the constraint that decides it)

Three facts in the current build force this shape:

1. A draft cannot be completed without **three evidence groups** (identity,
   residence and income). The residence group accepts `residence` and
   `identity` documents — an Aadhaar line carries the address, and extraction
   classifies such a document as identity — so the flow links the identity
   document there as well. Profile values can only be created by promoting a
   document.
2. Images are parked as `needs_attention` because **OCR is not implemented**, so
   only PDF/TXT can become evidence — and most people photograph their proofs.
3. Storage is **plaintext local disk**, there is **no retention scheduler**, and
   `/auth/export` returns only the account and consent records. Those are
   accepted only for synthetic data, by recorded decision (items 52, 54, 65).

Real documents therefore require the full WP2 gate, encryption at rest,
retention, complete export and probably OCR. Until then the pilot rehearses the
product; it does not process anyone's actual application.

## 3. Cohort

| Field | Decision |
|---|---|
| Size | 10–20 participants |
| Duration | 2–3 weeks, sessions of 25–30 minutes |
| Channels | Personal network; an NGO, community group or college; WhatsApp groups and social media |
| Mix to aim for | Self-applied vs agent-assisted; comfort with English; urban and semi-urban |
| Language | English only — the UI is not localised, and the script must say so |
| Exclusion | Anyone who wants to process a real application during the pilot |

Recruitment material must not promise approval, faster processing or government
affiliation, and must state that the session uses fake documents.

## 4. Session format

1. **Interview first (10 min), demo second.** Ask about the participant's last
   income-certificate attempt before showing the product, so answers are not
   anchored by the demo.
2. **Consent** (see `recording-consent.md`): notes, optional recording, support
   messages.
3. **Walkthrough (10–15 min)** with the participant driving, not the facilitator:
   home → sign-in (dev sign-in, described as a local prototype) → the three
   consents → vault upload of the two SPECIMEN PDFs → profile promotion and
   confirmation → service catalogue → draft, evidence links, declaration →
   export, pointing at the **"NOT a submission"** line.
4. **Close (5 min):** where would this help, where would it fail, what would you
   not trust it with, would you use it again, would you pay, what would you pay
   for.

Facilitator does not click for the participant. If they stall, note the stall
before helping — the stall is the finding.

## 5. What participants handle

- Two **SPECIMEN — SYNTHETIC** PDFs supplied by RINAVI (income and identity),
  generated for the pilot; a clearly fake 12-digit Aadhaar number may appear on
  the identity specimen and must never be a real one.
- A pilot account created with an email address they are willing to use.

They must not upload, type or dictate a real name, address, income or Aadhaar
number. If a participant brings a real document, the session stops (see §8).

## 6. Data collected, and not collected

| Collected | Why | Where |
|---|---|---|
| Account email | Sign-in and session | Application database |
| Passkey credential, if enrolled | Authentication | Application database |
| In-app synthetic data (documents, fields, profile, drafts) | The product under test | Database + vault volume |
| Consent records | Proof of purpose-scoped consent | Application database |
| Audit events | Security and support | Application database |
| Support messages/screenshots | Reproduce a blocker | Outside the system, pilot folder |
| Interview notes; optional audio | Findings and quotes | Outside the system, pilot folder |

**Not collected:** real documents, real Aadhaar numbers, portal credentials,
OTP codes, CAPTCHA solutions, location, contact lists, analytics or advertising
identifiers. No third-party analytics or error-reporting SDK is installed.

## 7. Success measures

| Measure | Definition | Target |
|---|---|---|
| Unaided completion | Participant reaches the export screen with no facilitator input | ≥ 70% of sessions |
| Time on task | Minutes from sign-in to export, stopwatch, recorded per session | Compared against a manual baseline: time to gather and fill the same packet by hand, measured once with a staff dry run |
| Trust | Answers to "would you use this for your own application?" and "would you pay?" | Qualitative; ≥ half positive |
| Blocker list | Every stall, misread label and abandoned step, with the screen | Ranked, not counted |

A session that ends in a blocker is a valid result. Do not coach a participant
through a step to make a measure look better; record the stall.

## 8. Stop conditions

- **A real document is offered:** stop, do not upload, delete anything already
  uploaded for that participant at their request, and record it as an incident
  in `docs/evaluation/` (no personal data in the record).
- **Portal credentials, OTP or CAPTCHA are mentioned:** refuse, explain the
  Assist-only boundary, and record the request as product feedback.
- **The participant withdraws consent:** stop recording, delete their media on
  request, and end the session.

## 9. Roles

| Role | Responsibility |
|---|---|
| Facilitator (owner) | Runs sessions, holds the pilot folder, deletes media on schedule |
| Grievance contact | Named in the privacy notice; currently the same person |
| Reviewer | The qualified adviser engaged for WP2 (not yet engaged) |

## 10. What this pilot does not prove

Extraction accuracy on real scans, real minutes saved on the official portal,
real conversion or willingness to pay at scale, and anything about portal
behaviour. Those need the real-documents gate.

## 11. Reopen trigger — promoting to a real pilot

This plan is superseded when **all** of the following hold:

1. The narrow review in this folder has been signed off and any required product
   changes have landed.
2. The full WP2 review (DPDP scope) is complete for real documents.
3. Encryption at rest, retention sweeps, complete export and a host with TLS
   have landed (checklist items 64, 68, 65, 58, 97, 98).
4. A decision on OCR and localisation is recorded, because most real proofs
   arrive as photographs and the UI is English-only.

Until then, any real-document request is out of scope and is handled by §8.

## 12. Open decisions for the review

- Recording tool and where recordings live (local disk vs an encrypted volume).
- Whether a support channel outside the app is acceptable, and on what device.
- Whether participants may keep the account after the pilot or it is deleted at
  the end (recommended: deleted, with the deletion date told to them up front).
