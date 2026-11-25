# Baseline metrics

**Status:** draft instrument, 2026-11-24. Item 82 asks for *baseline metrics*;
this file defines three, precisely enough that the measurement actually happens
and honestly enough that the result cannot be overclaimed.

## The three baselines

| Baseline | Answers | Source | When |
|---|---|---|---|
| **A. Demand** | How bad is the problem, in numbers? | Interview notes | Continuously; reported at session 20 |
| **B. Manual packet** | How long does the same paperwork take by hand? | One staff dry run | Once, before the first pilot session |
| **C. Product** | Does the prototype beat it? | Pilot sessions | `../compliance/pilot-plan.md` §7, unchanged |

A and B are item 82's deliverables. C belongs to the pilot; this file only says
how to record it consistently, because B is meaningless without it.

## A. Demand baseline

Computed from the notes, one row per participant, reported as medians and
shares with `n` beside every figure.

| Measure | Definition | Unit |
|---|---|---|
| Recency | Months between the last attempt and the session | months, median |
| Elapsed time | Start of the attempt to certificate in hand, or to abandonment | days, median, split completed vs abandoned |
| Working time | Time the participant actually spent doing it (not waiting) | hours, median, self-reported band |
| Trips | Physical visits to any office, notary, bank or CSC | count, median |
| Cost | Fees + agent + travel + leave, in bands | ₹ band, median band |
| Agent share | Participants where a paid agent did any step | % |
| Rejection share | Participants whose attempt was rejected or returned at least once | % |
| Document burden | Documents the participant had to produce | count, median |
| Missing documents | Documents they did not hold and had to obtain | count, median |
| Abandonment | Participants who stopped and did not finish | % |

Bands, not figures. If someone volunteers an exact income or fee, record the
band it falls in, not the number — the same rule as 05's writing rules.

Report the split that matters: **self-applied vs agent-assisted**. A single
median across both groups describes nobody.

## B. Manual packet baseline

This is the number "time on task" is compared against. Get it wrong and the
pilot's headline comparison is fiction, so the procedure is fixed.

### The packet

Exactly what the product asks for, no more:

- Two documents: one **identity** SPECIMEN PDF and one **income** SPECIMEN PDF
  (`pilot-plan.md` §5).
- Five required values copied from them: applicant name, father's/husband's
  name, date of birth, residence address, annual income.
- The purpose field, and occupation if volunteered.
- The declaration, read and signed: *"I declare that the particulars given in
  this application are true and complete…"* (the wording in
  `catalog/services/edistrict/income-certificate/versions/1.0.0/service_pack.json`).

Print the form fields from that pack's `form_template` so the labels match what
the product shows. A different layout measures a different task.

### The procedure

| Step | Rule |
|---|---|
| Start | The two PDFs and a blank printed form are on the table. Say: *"Fill this in from these two documents and sign the declaration."* Start the stopwatch on the last word |
| Stop | The last required field is written and the declaration is signed. Stop the stopwatch |
| Excluded | Printing, travel, portal time, waiting, and obtaining the documents. State this in the report |
| Runs | Three, same person, same day, same table. Median is the figure. If the three spread by more than 20%, run twice more and use the median of five |
| Covariate | Record whether the person has filled the real form before. Run both a first-timer and a practised person if possible, and report both — the pilot's participants are first-timers |
| Record | Date, role (not name), conditions, the three times, the median |

### The record

```text
Manual packet baseline — date: __________
Person: role ______  has filled the real form before: yes / no
Our source: printed form from pack 1.0.0, two SPECIMEN PDFs
Run 1: __ min __ s   Run 2: __ min __ s   Run 3: __ min __ s
Median: __ min __ s     Spread: __%      Additional runs: ________
Conditions (lighting, interruptions, printer): ______________________
```

## C. Product measures, recorded the same way

`pilot-plan.md` §7 is authoritative; this is the recording discipline, not a
redefinition.

| Measure | Record | Beware |
|---|---|---|
| Unaided completion | One yes/no: did they reach the export control with zero facilitator input? If no, the screen where they stopped | Do not count a nudge as unaided. Do not count a session where item 102 was not deployed |
| Time on task | Stopwatch, sign-in to export, whole minutes | Pauses for questions count; a participant who gives up has no time, and is recorded as a non-completion, not a fast one |
| Trust | The two answers verbatim | Do not paraphrase into a rating |
| Blockers | Each with the screen and the second | Ranked, never counted as a single number |

## What the numbers may and may not be used to claim

**May:** "Hand-filling the same packet took a median of M minutes (n=3, staff);
in the pilot, N of 20 participants reached the export control unaided, median
time on task P minutes."

**May not:**

- "Saves X minutes at the portal." The baseline excludes travel, waiting and
  portal time, and the pilot never touches the portal.
- "Faster approval", "fewer rejections", "higher approval rate". Nothing here
  observes a real application or a department decision.
- "X% faster than the government process." There is no measured government
  process; there is one staff dry run at a table.
- A single "time saved" figure across the whole cohort without the
  self-applied/agent split.

The comparison the pilot earns is narrow and useful: **preparing the packet by
hand versus preparing it in the prototype**, for someone reading it for the
first time. Say exactly that.

