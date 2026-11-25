# Service scorecard

**Status:** draft instrument, 2026-11-24. Fill it once six sessions exist and
finalise it at session 20. Item 82's *service/geography selection* is the output;
this file is how that selection is justified instead of guessed.

## What is being scored

A **candidate service** — a government certificate or application a citizen
prepares offline and submits at a portal. RINAVI's next pack is one of these.
The baseline is Delhi's income certificate: it is built, so it calibrates the
scale, and its scores come from the code, not from impressions.

| Candidate | Why it is on the list | Evidence state |
|---|---|---|
| Income certificate (Delhi) | Built; the calibration row | Code + sessions |
| Domicile certificate (Delhi) | WP9's recorded first choice (item 86) | Sessions only |
| Caste certificate — SC/ST | Same department, heavy document burden | Sessions only |
| OBC certificate | Related to caste, different evidence rules | Sessions only |
| EWS certificate | Income-adjacent; the pack could reuse bindings | Sessions only |
| Birth certificate | Different department, different failure mode | Sessions only |
| Ration card | High volume, address-linked, often agent-mediated | Sessions only |
| Old-age pension | Income and age linked; recurring, not one-off | Sessions only |
| NSP scholarship | The demand driver for income certificates | Sessions only |
| CPGRAMS grievance | Not a certificate; score separately or exclude | — |

CPGRAMS is on the list because citizens mention it, and off the ranking because
it is a complaint channel, not an application. Do not mix the two rows into one
total.

## The eight criteria

Weights sum to 100. Score 1–5; anchors below; `?` where there is no evidence.

| # | Criterion | Weight | 5 | 3 | 1 | Evidence |
|---|---|---|---|---|---|---|
| 1 | Demand | 20 | 8+ of 20 sessions mention it unprompted | 3–7 | 0–2 | Session tags + §6 close answers |
| 2 | Document burden | 15 | 2 documents, both commonly held | 3 | 4+, or documents most applicants do not hold | Interview §1 document column |
| 3 | Online completeness | 15 | Apply, pay and receive fully online | Apply online, collect or verify in person | Must appear in person; agent-only in practice | Official portal, checked and dated |
| 4 | Portal friction | 10 | One short session, one upload | Several uploads or retries typical | Sessions time out, common formats rejected | Interview §3, `DEVICE` and `FILL` tags at the `UPLOAD` step |
| 5 | Rejection and correction pain | 15 | Rejection rare; correction is an online edit | Rejection common; correction means a new application | Correction needs an office visit or an agent | Interview §3, `RETRY` tags at the `CORRECT` step |
| 6 | Agent dependence | 10 | Most applicants self-apply | Mixed | Most use an agent | Group split in 02 |
| 7 | Legal fit and risk | 10 | No Aadhaar dependency beyond display; pack authorable from public sources | Aadhaar or a sensitive field involved, handled per A1 | Needs a document RINAVI must not handle, or an unanswered policy question | Item 83, `data-map.md`, ADR-0003 |
| 8 | Build cost | 5 | Reuses existing bindings; one new pack | New classifications or extraction rules | A new module or a portal relationship | The pack format, `catalog/services/**` |

## Rules that keep the score honest

1. **Criterion 3 is a gate, not a weight.** A service that scores 2 or less
   cannot be the next pack, whatever its total. RINAVI prepares a submission
   the citizen makes online; an offline-only service turns the product into a
   form-filling service with no destination.
2. **`?` is not 3.** Where a criterion has no evidence, mark `?` and compute two
   totals: best case (all `?` = 5) and worst case (all `?` = 1). If the ranking
   flips between them, the scorecard has not decided — run more sessions.
3. **Every score cites evidence.** A 5 on demand cites session codes; a 4 on
   portal friction cites the official page and the date it was read. A score
   with no citation is struck out.
4. **The owner may override the ranking once, in writing,** with the reason.
   The override goes in the decision ledger (09) and the findings report.
5. **Do not score a service you have not heard a participant describe.** Public
   sources can fill criteria 3, 4 and 7; they cannot fill 1, 2, 5 or 6.

## The sheet

```text
Candidate: ______________________  Scored on: __________  By: ______
Evidence: sessions ______ (codes), official pages ______ (dates)

1 Demand            __ x 20 = __   citations:
2 Document burden   __ x 15 = __   citations:
3 Online complete.  __ x 15 = __   citations:            DISQUALIFIER <= 2
4 Portal friction   __ x 10 = __   citations:
5 Rejection pain    __ x 15 = __   citations:
6 Agent dependence  __ x 10 = __   citations:
7 Legal fit         __ x 10 = __   citations:
8 Build cost        __ x  5 = __   citations:

Total (known) ____   Best case ____   Worst case ____   Rank: __
Known gaps (`?` criteria):
```

## Geography

Scored separately, and only from the sample. Three questions:

| Question | Evidence | Rule |
|---|---|---|
| Where do the participants live? | 02's mix, session notes | If 90% or more are one state, the selection is that state — and the report says the sample cannot support another |
| Does the state's portal publish the process, fees and document list? | Official pages, dated | No published process means no pack can be authored honestly |
| Is a pack authorable without a portal relationship? | `catalog/services/**`, A0 register | Yes for every state in scope today; nothing else is A0 |

**No extrapolation.** Twenty interviews in Delhi justify Delhi. They do not
justify "and the same will hold in Bihar", and the findings report must say so
in one sentence.

## Calibration

Score the income certificate first, from the code and from the sessions. It
should land mid-range: strong legal fit and demand, weak portal friction and
agent dependence. If it scores 5 across the board, the anchors are being read
as hopes, not evidence — recalibrate before scoring a candidate the founder
wants to win.

