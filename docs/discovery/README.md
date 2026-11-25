# Discovery kit — instruments for WP1 (item 82)

**Status:** draft instruments, no evidence yet. **Date:** 2026-11-24, against
`main` @ 71b5023. **Owner:** the founder runs every session.

Checklist item 82 is one line — *20–30 citizen interviews, service scorecard,
service/geography selection, baseline metrics* — and until now nothing in the
repository said how to produce any of it. This folder is the how.

## What this is, and what it is not

- **It is the instruments.** Briefing, recruitment, interview guide,
  facilitator script, note template and coding scheme, service scorecard,
  baseline definitions, exit criteria, rollup. Nothing here is a finding.
- **It is not the pilot.** The synthetic pilot is 10–20 participants working
  through the product with SPECIMEN documents (`../compliance/pilot-plan.md`).
  Discovery comes first and studies the **problem**: what a participant's last
  real attempt cost, where it broke, and which service deserves the next pack.
- **It is not permission to collect data.** Item 83 is untouched. No session
  accepts a real document, a real Aadhaar number, a portal credential, an OTP
  or a CAPTCHA solution, and no session opens a government portal.

## The nine instruments

| # | File | What it decides |
|---|---|---|
| 1 | `01-participant-briefing.md` | What a participant is told before anything is asked |
| 2 | `02-recruitment-and-screening.md` | Who is invited, who is excluded, and how the mix is held |
| 3 | `03-interview-guide.md` | The questions, the probes, and what a usable answer sounds like |
| 4 | `04-facilitator-script.md` | The 45 minutes, minute by minute, including the stall and stop rules |
| 5 | `05-note-template-and-coding.md` | What one session's note contains, and the fixed tags that make 20 notes countable |
| 6 | `06-service-scorecard.md` | Which service and geography the evidence nominates, and on what weights |
| 7 | `07-baseline-metrics.md` | The three baselines, defined precisely enough to measure |
| 8 | `08-exit-criteria.md` | What closes item 82 — and what does not |
| 9 | `09-rollup-template.md` | How findings become decisions instead of a folder of notes |

## The two rules that keep this publishable

1. **Instruments here, observations elsewhere.** A participant code (P01, P02,
   …), never a name, email, phone number, street address, Aadhaar number,
   application number or income figure. Not in a quote either. The GitHub Pages
   site serves this whole `docs/` tree (`../compliance/wp8-pilot-readiness.md`,
   Track B follow-up 8), so this folder is public to the internet.
2. **A quote is used only if that participant ticked the quotes box**
   (`../compliance/recording-consent.md` §1), and even then it is attributed as
   "P07". No exceptions for a particularly good sentence.

Private material — contact list, consent forms, notes, recordings, screenshots —
lives in the pilot folder on one machine, outside the repository, per
`../compliance/recording-consent.md` §3.

## Dependencies

| Depends on | Why |
|---|---|
| `../compliance/recording-consent.md` | The consent form, the retention periods and the withdrawal promise. Used unchanged; see the wording question below. |
| `../compliance/pilot-plan.md` §3–§8 | Cohort mix, stop conditions and the pilot's measures. Where discovery and pilot overlap, the pilot plan is authoritative. |
| `../architecture/decisions/0006-localisation.md` | English is the language of record. No ad-hoc translation of the notice, the consent form or the product's own words. |
| `../planning/v1-checklist.md` item 102 | The pilot's headline measure is *reaches the export control*. If item 102 is not deployed at session time, record "not collectable" — never a soft yes. |
| `../compliance/portal-permission-register.md` | Access level A0: no portal is opened during a session, for the participant or with them. |

## Order of use

1. Recruit and screen with 02, keeping the mix in 02's table.
2. Send or read 01 before anything else happens.
3. Take consent with `recording-consent.md` §5 — before the interview, not
   after it.
4. Run 04's 45 minutes. Ask 03's questions; do not skip the interview to reach
   the demo.
5. Write the note in 05's template the same day, and code it.
6. Roll up weekly with 09 so the coding stays comparable.
7. Score candidates in 06 once six sessions exist, not before — and again at
   the end.
8. Measure 07's manual baseline once, before the first pilot session.
9. Close against 08, then publish the public-safe summary under
   `../evaluation/` and tick item 82 in the same PR.

## Where the outputs go

| Output | File | Destination |
|---|---|---|
| Findings report, category level | `discovery-findings-YYYY-MM-DD.md` | `docs/evaluation/`, public |
| Scorecard, filled | Private annex, copied minus participant detail | Private folder; the ranking and its evidence counts are public |
| Service/geography selection | One page, decision + rationale + what would change it | `docs/evaluation/` or a checklist note |
| Baseline figures | In the findings report, with n | `docs/evaluation/` |
| Notes, quotes, recordings, consent forms | — | Private pilot folder only |

## One wording question for the WP2 reviewer

`recording-consent.md` §5 is titled *RINAVI pilot — recording and notes*, and
discovery participants are not pilot participants. The kit's recorded choice is
to use the form unchanged and say at handover that this is the **discovery round
of the pilot study** — one reviewed text instead of two. Each note records which
instrument version was used. The reviewer should confirm or reject this at B3; if
rejected, the fix is one line in that file's title and a reprint, not a new
instrument.

## Status

These instruments have not been used in a session. The first three sessions are
the test: after the third, read 05's notes back and ask whether two different
facilitators could have produced comparable ones. If not, fix the template
before session four, and say so in the findings report.

