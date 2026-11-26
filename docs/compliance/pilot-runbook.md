# Pilot operations runbook

**Status:** draft v1, 2026-11-24, against `main` @ `71b5023`. Item 84's operating
plan. Not approved for a first session yet — see the gate table in §3.

This is the document an operator follows. It does not restate the policy, and
where it and a policy document disagree, the policy wins:

| Question | Authority |
|---|---|
| Who takes part, what happens in the 25–30 minutes, what success means | `pilot-plan.md` §3–§8 |
| What is stored, where, and which purpose gates it | `data-map.md` |
| How long anything is kept, and what survives deletion | `retention-policy.md` |
| What a participant is told and what they sign | `privacy-notice-draft.md`, `terms-draft.md`, `recording-consent.md` |
| Which portals are in scope and at what access level | `portal-permission-register.md` (all A0) |
| What is accepted and what reopens it | `wp8-pilot-readiness.md` |
| What evidence WP1 owes and how it is gathered | `../discovery/` (item 82) |

## 1. Roles

| Role | Who | Decides |
|---|---|---|
| Facilitator / operator | The owner, every session | Pause or stop a session; whether the next session runs |
| Support | A second person on a named channel, not the facilitator mid-session | Nothing during a session; triages between sessions |
| Engineering | YooExE | Fixes, the wipe script, the backup drill |
| Compliance owner | The owner, with the qualified reviewer for item 83 | Whether a change reopens the legal gate |

One person may hold both facilitator and support, but not simultaneously: if
the facilitator is also the support channel, a participant who emails mid-
session gets no answer and the runbook's response promise is false. Name the
support person and the hours in §7 before the first session.

## 2. Topology, and the sign-in mode that decides the gate

D1 fixed the shape: **remote-supervised sessions, participants on their own
devices**, hosting moving along the ladder in ADR-0004 — rung 2 is a Cloudflare
Tunnel for pilot sessions, rung 3 a VM behind a reverse proxy, and nothing
internet-reachable until item 83 clears.

The walkthrough (`pilot-plan.md` §4.3) signs the participant in with the **dev
sign-in**, and that forces the environment: `dev_signin_enabled` is refused
outside `development` (`core/config.py::_reject_unsafe_production`). In
development the production posture is off — dev sign-in is live, `/docs` and
`/openapi.json` are registered, and the cookie-secure and https-WebAuthn checks
are skipped. A tunnel changes reachability, not posture: it publishes the
origin, so the gate has to be something other than a longer cable.

**D10, decided 2026-11-25: a pilot sign-in mode (option B).** Three candidates
were on the table:

| Candidate | What it defended | Why it is not the answer |
|---|---|---|
| Edge gate — Cloudflare Access (one-time PIN or allow-list) | The public, in front of the tunnel | Gates *access*, not *identity*: the app behind it still signs in any email typed into it, so two participants can still land on one account — and the posture behind the gate is still development mode |
| Edge gate without a domain — basic auth over a quick tunnel | The same, for free, in an hour | A shared credential with no audit trail, and browser auth dialogs fail inside the in-app browsers participants open links from |
| **Pilot sign-in mode — chosen** | Both, inside the app | Two days of code (#103), because the mode has to exist before the first session |

Cloudflare stays as transport (rung 2): TLS, DDoS, the ephemeral hostname. It is
not the gate, so G4 no longer asks for one in front of the tunnel.

**What the mode is.** `RINAVI_ENVIRONMENT=production` with the guards on —
`cookie_secure`, https `webauthn_origin`, no `/docs`, no `/openapi.json` —
`dev_signin_enabled=false`, and `pilot_invites_enabled=true`. With that flag on,
the only way in is a single-use invite the facilitator issues on the host:

- **Issue** — one command prints a URL for one session. TTL 15 minutes; the
  participant is on the call when it is issued; the token never reaches the
  audit log or the HTTP log.
- **Consume** — the URL creates a fresh synthetic identity
  (`pilot+P07@rinavi.test`, one per session label) and burns the invite.
  Identity is granted, not typed, so two participants cannot collide by
  sharing an address.
- **Re-issue and revoke** — one command each. Re-issuing invalidates the
  previous invite for that label, which is what a participant whose in-app
  browser reloaded mid-flow needs; revoking ends access immediately.
- **Attribution** — the sign-in's audit row carries the session label, so the
  log answers *which participant*, not *someone behind the gate*.
- **Off, then retired** — the flag is false outside pilot runs and is refused
  together with `dev_signin_enabled`; the path is retired at pilot close (#103)
  rather than left as a second sign-in.

**One identity per participant, always.** The invite now creates the identity,
so the rule is structural rather than procedural: one invite, one session, one
account. It still depends on the wipe in §5 — a reused label reuses the
account, which is why the wipe is not optional.

**G4 clears only when the mode is built and used from a device that is not the
facilitator's, off the network, with cookies cleared.** An invite working on the
facilitator's laptop proves nothing.

## 3. Before the first session — the gate

No session runs until every row is CLEARED or explicitly accepted with a
reopen trigger. Status is re-checked the day before, not copied from here.

| # | Gate | State | Owner |
|---|---|---|---|
| G1 | Item 82 evidence exists — the problem is understood before the product is tested | BLOCKED, no sessions run | Owner (`../discovery/`) |
| G2 | Item 83 qualified review has signed off | BLOCKED, external | Owner → reviewer |
| G3 | Host chosen and deployed, TLS terminating at the proxy, one worker | PENDING, ADR-0004 ladder | Owner + YooExE |
| G4 | Pilot sign-in mode live (§2, D10): production posture, `dev_signin_enabled=false`, `pilot_invites_enabled=true`, and a single-use invite signs a fresh participant in from a device that is not the facilitator's, off the network | BLOCKED on #103 — decided, not built | YooExE + Owner |
| G5 | `RINAVI_STORAGE_DIR` known and recorded, with `RINAVI_STORAGE_ENCRYPTION_KEY_FILE` beside it and a copy of the key outside the vault; one worker; rate-limit storage `memory://` documented as single-process | CLEARED in config, values PENDING with the host | YooExE |
| G6 | The wipe in §5 rehearsed against a throwaway account on the host, with the verification command in the log | PENDING — script half is YooExE's | Owner + YooExE |
| G7 | Backup and restore drill — YooExE's task A7 — done, **including the blob key**; until then "deleted" is final and a disk failure is total loss | PENDING | YooExE |
| G8 | Support person, channel and hours named in §7 | PENDING | Owner |
| G9 | Consent forms printed twice, private folder path recorded, session log created, recording tool decided | PENDING, cheap | Owner |
| G10 | Blob encryption at rest (item 101) | **CLEARED in code** — AES-GCM blobs, production refuses to start without a key. For synthetic sessions it is not a gate; it is the gate the moment a real document is involved, and the key then needs G5, G6 and G7 behind it | YooExE |
| G11 | Participants are 18 or over | **CLEARED** — question 1 of the screening script asks it as a yes/no; a minor stops before consent is taken | Owner |

G10 is deliberately in this table as a non-gate: it is the row most likely to be
mistaken for one. The pilot's documents are marked SPECIMEN, and the privacy
notice says so. Add a real document and this row flips to BLOCKED.

G11 is a gate because D1 put children's data on the real-data horizon (an income
certificate is often requested for a scholarship, and the applicant can be a
minor). Verifiable parental consent is not set up, so the pilot stays adults
only; a minor's session is out of scope until that changes, and a participant who
turns out to be under 18 stops before consent is taken. The screening script
(`../discovery/02-recruitment-and-screening.md`) now asks the question directly,
first, before anything else about the attempt.

## 4. Session lifecycle

| When | Do | Where it is recorded |
|---|---|---|
| T−1 day | Confirm time and channel; send the participant briefing (`../discovery/01-participant-briefing.md`); check the host is up and the gate still rejects an unauthenticated request | Session log |
| T−30 min | Fresh synthetic email created for this participant; storage directory listed and its current contents noted; export folder emptied; consent form printed | Session log |
| T−0 | Run `pilot-plan.md` §4: interview first, consent, walkthrough, close. `../discovery/04-facilitator-script.md` §1–§3 and §5 apply unchanged; its demo section is this pilot's walkthrough | Note, same day |
| T+0 | **Wipe (§5) before anything else.** The next participant's identity is created after the wipe, never before | Wipe log |
| T+2 h | Note written and coded (`../discovery/05-note-template-and-coding.md`), measures entered | Note |
| T+5 days | Nothing is due; do not re-open the note. Corrections are appended, dated | Note |
| Weekly | Gate re-check (§3); storage directory count reconciled against the session log; recordings labelled | Runbook check |

## 5. The wipe — between participants

Run this after **every** session, including a session that ended badly. The
default is that no participant's account outlives their session; the
alternative (participants keep accounts) is an open decision in `pilot-plan.md`
§12, and choosing it means changing `retention-policy.md` first, not this list.

| # | Step | Expect | If it fails |
|---|---|---|---|
| 1 | Sign out in the app, then close every tab on the pilot origin | Session cookie gone | Clear the cookie for the origin in the browser's storage settings; note it |
| 2 | Account screen → delete account | Redirect to sign-in, and `DELETE /auth/account` returns 204 | 503 means the storage purge failed and the account was kept. Retry once. A second failure stops the pilot: do not start the next participant |
| 3 | Verify the participant's storage directory is gone | `$env:RINAVI_STORAGE_DIR` contains only the directories of accounts that should still exist — none for this participant | If it is still there, the purge did not run; stop and escalate. Do not "delete it in Explorer" and move on: the row and the blob would then disagree |
| 4 | Delete the exported JSON from the downloads folder | The file is gone. It contains the account export the participant saw | — |
| 5 | Delete the browser profile or clear storage for the origin | Next sign-in starts clean | Use a dedicated profile per session and delete it; do not reuse the facilitator's main profile |
| 6 | Write the wipe line | Participant code, time, 204/503, directories remaining, export file deleted | — |

**The key.** The blobs are ciphertext, but one key unlocks every account's files
and it survives the per-session wipe. So a directory left behind is still
readable, to the app and to anyone holding the key: delete the directory anyway.
The key is destroyed only at close-out (§6, step 3). After that, ciphertext left
on the disk has no reader.

What the wipe does **not** remove, and why that is acceptable here:

- **Audit rows.** They survive account deletion by design (`retention-policy.md
  §3`), with the actor link severed and the details redacted — an email on
  `account.deleted` is replaced before storage (`data-map.md` §audit). They are
  the security record and the only way to investigate an incident. They are also
  the reason the close-out in §6 ends with dropping the database.
- **The participant's own browser history**, if they used their own device and
  the facilitator screen-shared nothing. Say in the close that they can clear
  it; do not remote into their machine to do it.

### Wipe log (private folder, one line per session)

```text
P-code | date | delete 204/503 | dirs remaining after | export file deleted |
browser profile deleted | facilitator initials | note
```

## 6. Pilot close-out

`retention-policy.md` §6 is the authority; the operator's version:

1. Tell every participant the deletion date in writing, before it happens.
2. Delete every remaining account through the app (the tested path).
3. Stop the app, delete the vault directory **and the key file**, drop and
   recreate the database — the key deletion is what makes any ciphertext left on
   the disk unreadable, and the database drop is the only way to clear audit rows.
4. Delete the pilot folder (notes, recordings, screenshots) and record the
   deletion in `../evaluation/` with no personal data.
5. Write the completion date into the session log and the wipe log.

Step 3 has no script yet (`retention-policy.md` §5). Until YooExE's wipe script
exists, step 3 is manual and must be done with the app stopped — doing it while
the app runs is how a blob is orphaned.

## 7. Support

| Field | Value |
|---|---|
| Channel | *to be named before G8 closes — one channel, not "DM me anywhere"* |
| Hours | *working hours only; say so in the briefing* |
| First response | Next working day. Nothing in a 25-minute pilot session is an emergency except an incident (§8) |
| Owner | *named person with the hours above* |

**Support may:** explain a screen, ask what the participant saw, reschedule,
take a bug report with a screenshot of the prototype, point at the export
caveat.

**Support may never:** accept a document through any channel, ask for a
password or an OTP, submit anything anywhere, promise an outcome, or remote
into a participant's device. A document offered in support is refused in one
sentence and deleted; the refusal is logged as an incident, not a ticket.

Canned replies, used verbatim:

> "Thanks — can you tell me which screen you were on and what it said? Please
> don't send any document or ID number."

> "That's a known limitation of the prototype: it starts a draft for you and
> you submit it yourself at the official portal. It can't submit for you."

> "We can book another slot on [date]. The prototype has no saved progress, so
> you'd start from the beginning."

The third reply is only true while the wipe runs after every session. If a
participant's account is kept, the sentence changes — another reason the
default is deletion.

## 8. Incidents

| Level | Definition | Response |
|---|---|---|
| **S1** | A real document, real Aadhaar number, portal credential, OTP or other real personal data entered the system | Stop the session. Delete the document and the account immediately (the 204 path). Record in the incident log with no personal data. Facilitator tells the owner the same day; the owner decides whether the privacy notice, the exported findings or the accepted-risk list changes |
| **S2** | Data unavailable or lost — a 503 purge, a missing blob, a failed delete, a wiped database | Stop the pilot until the cause is known. Nothing is retried more than once. Record |
| **S3** | A session blocked — host down, sign-in broken, upload rejected, gate locked out | Reschedule; if it recurs across two sessions, the next session does not run until fixed |

An incident is recorded even when nothing was exposed, and the record never
contains the participant's data. If an S1 involves data the participant
supplied, tell them what was deleted and when; do not describe the system's
internals to them.

## 9. Rule updates — keeping the pack true

The pilot's knowledge of the service is the pack
(`catalog/services/edistrict/income-certificate/`): fee, indicative processing
time, the four checklist groups, the eight form fields and the declaration.
Every one of those can change without RINAVI noticing, and a session then tests
a product that is confidently wrong.

**Monthly, and before any session after a gap of two weeks:**

1. Open both sources listed in `service.json` (`edistrict.delhigovt.nic.in`,
   `revenue.delhi.gov.in`) and re-read the fee, the processing time, the
   document list, the form fields and the declaration.
2. Compare against `versions/<latest>/service_pack.json` and `service.json`.
3. Classify any difference: **documents** (checklist groups), **fields**
   (form template), **money/time** (metadata), **wording** (declaration or
   official-channel steps), or **URL** (a source moved).
4. If something changed: bump `pack_version` (minor for wording, major for
   documents or fields), update the pack and `service.json` together, run the
   loader test, and record the change and the date in the session log's
   "pack in use" column.
5. If the change is material and cannot be re-verified before the next
   session — a new document requirement, a fee, a changed declaration — **pause
   sessions for that pack** rather than run them against a stale pack.

D5 already nominates `last_verified` as an optional pack key, and it lands with
YooExE's loader work (B7's prerequisite). Until a pack carries the field, the
session log's "pack in use" column is the record — and a session run against a
pack whose date cannot be shown should not be counted as evidence that the pack
is current.

The pilot never opens the portal, so a portal outage cannot break a session. It
only makes the official-channel guidance harder to confirm; if the portal is
down when a participant asks what to do next, the answer is "submit it there
yourself when it is back", not a phone number you found in a search result.

## 10. Measurement

`pilot-plan.md` §7 defines the four measures. The operator's job is recording
them the same way every time:

| Measure | Recorded | Definition (do not improvise a second one) |
|---|---|---|
| Unaided completion | Yes/no + the screen where they stopped | Reached the export control with zero facilitator input. A nudge is not unaided. If item 102 is not deployed, record "not collectable" |
| Time on task | Stopwatch, whole minutes | First click on the pilot origin to the export control. Pauses for questions count. A participant who gives up has no time and is a non-completion |
| Trust | The two answers verbatim | Never a rating you assign |
| Blockers | Ranked, each with screen and second | Never summarised as a count |

The comparison number — the manual packet baseline — is defined in
`../discovery/07-baseline-metrics.md` §B and is measured once with a staff dry
run. Do not compute it from pilot sessions.

## 11. Backup and restore

**PENDING — backup drill (YooExE task A7, gate G7), YooExE.** There is no
backup today, so "deleted" is final (`retention-policy.md` §5). Before the
pilot starts, the drill must show: a database backup taken, the app restored on
a clean volume, the restored data readable, **the restored blobs readable with
the saved key**, and the restore time recorded. A backup that omits
`RINAVI_STORAGE_ENCRYPTION_KEY_FILE` restores rows that point at ciphertext
nobody can open. Until then, a disk failure during the
pilot loses the pilot — which is acceptable for synthetic data and unacceptable
as a launch posture, so it is a WP11 item (85) as well as a pilot gate (G7).

## 12. What this runbook does not cover

- **Recruiting participants** — `pilot-plan.md` §3 and
  `../discovery/02-recruitment-and-screening.md`.
- **The questionnaire** — `../discovery/03-interview-guide.md`.
- **The consent interview** — `recording-consent.md` §6.
- **A real document, real Aadhaar value or portal session** — out of scope until
  item 83 and item 101 clear.
- **Pricing, support SLAs beyond the pilot, and hosting cost** — WP11.
- **Production hardening** — the development-mode posture in §2 is a pilot
  compromise, not a deployment plan.

## Review trigger

Rewrite this runbook when any of these changes: the topology in §2, the wipe
script, the backup drill, the pack schema, the pilot plan's measures, or the
first real document. Each is a change to what an operator does under pressure.

