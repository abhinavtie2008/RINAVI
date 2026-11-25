# Exit criteria

**Status:** draft instrument, 2026-11-24. These are the pass conditions for
checklist item 82. The box stays unticked until every one holds; the PR that
ticks it links the evidence for each.

## The conditions

| # | Condition | Passes when | Evidence |
|---|---|---|---|
| E1 | Sessions | 20 completed (30 maximum), with 02's minimums met — or the shortfall named and justified in the report | Session log, counts per group |
| E2 | Coding | Every note coded with the fixed vocabulary; at least one findings line per session; quotes only where consented | Notes, rollup |
| E3 | Saturation | The last five sessions introduce no new friction tag and at most one new step/tag combination | Rollup's weekly counts |
| E4 | Scorecard | At least six candidates scored, each score citing sessions or a dated official page; ranking stable across best/worst case, or the gap explained | 06, filled |
| E5 | Selection | Service and geography written down with a rationale and one line of *what would change this* | One page, `docs/evaluation/` or checklist note |
| E6 | Baselines | Demand baseline computed with `n`; manual packet baseline run three times, median recorded with date and covariate | 07's records |
| E7 | Hygiene | Recordings deleted or dated; consent forms filed; every pilot account wiped and logged; no participant data in the repository | Deletion log, account log, a grep of the diff |
| E8 | Publication | Public-safe findings report in `docs/evaluation/`, private annex indexed privately, item 82 ticked in the same PR with a note naming E1–E7 | The PR |

## What does not close item 82

- **Twenty sessions alone.** The item asks for four outputs; sessions are the
  input to three of them.
- **A scorecard with no citations.** Research from public pages can fill
  criteria 3, 4 and 7. It cannot fill demand, document burden or agent
  dependence, and a total built only from public pages is a guess with
  arithmetic.
- **A demo-only set.** If every session skipped the interview, the kit produced
  usability notes, not discovery evidence.
- **Twenty people from one WhatsApp group.** The mix in 02 exists so the answer
  is not "the founder's friends would use this".
- **A satisfaction score.** Nothing in this kit measures satisfaction, and
  adding a rating at the end does not convert opinions into evidence.

## The stop rule

At 30 sessions, stop even if E3 is unmet. Record why in the report: either the
sample had genuinely not saturated — which is itself a finding about how varied
the process is — or the last sessions were repeats. Do not run to 40 to make a
table look complete; the scorecard's denominator is the design, not a target to
beat.

## What each condition unlocks

| Once | Then |
|---|---|
| E1–E8 hold | Item 82 ticks; WP8 pilot operations (item 84) can be planned on evidence; the pilot plan's cohort and script get a v2 informed by where people actually stalled |
| E4–E5 hold | WP9's second-service nomination (item 86) is justified, or *domicile first* is overturned with a reason |
| E3 plus the language findings | The Hindi priority question (item 100, ADR-0006) gets a number instead of an assumption — how many sessions could not proceed on English alone |
| E7 holds | The discovery promises are closed: recordings gone on schedule, accounts wiped, nothing participant-derived in public |

Item 87 (guided-fill extension) stays blocked regardless: it needs item 83's
portal-permission register, not discovery evidence.

## Before the first session

Three things that are not evidence but are prerequisites, and each has bitten
a study before:

1. **The consent form is printed twice** and the deletion date is written on it
   before the participant leaves.
2. **The private folder exists** and its path is recorded somewhere you will
   find in three months.
3. **The reviewer question is on the agenda** — does `recording-consent.md`
   cover discovery sessions unchanged (the kit's choice), or does it need a
   separate form? Ask at B3; the answer changes one line, not the study.

