# Note template and coding scheme

**Status:** draft instrument, 2026-11-24. One note per session, written the same
day. The note is the only durable record; the recording is deleted at 90 days
and the memory is gone by the weekend.

## Why a fixed template

Twenty free-form notes produce twenty stories and no denominator. Twenty notes
with the same fields and the same tags produce a frequency table, which is what
the scorecard and the exit criteria need. The template is deliberately
boring — it is a form, not a diary.

## The note

```markdown
P-code: P07              Date: 2026-12-01        Channel: video / in person
Language: English (all)  or  Hindi (interview) + English (consent, demo)
Facilitator: ______      Consent instrument: recording-consent.md, 2026-11-19
Consent: notes Y/N · audio Y/N · screen Y/N · video Y/N · quotes Y/N · screenshots Y/N
Deletion due: 2027-03-01        Deleted on: __________
Group: self-applied / agent-assisted / abandoned-before-applying / insider
Prior applications: first / repeat (n = __), last one when: ______

## 1. The attempt, in order
| # | What they did (their words where possible) | Channel | Time | What they had to produce |
|---|---|---|---|---|
| 1 | | portal / CSC / office / agent / family | | |

## 2. Cost
| Fees | Agent | Travel (trips) | Leave taken | Total band | Who paid |
|---|---|---|---|---|---|
| | | | | | |

## 3. Where it broke
| # | What happened | Their words | What they did next | Severity |
|---|---|---|---|---|
| 1 | | | | BLOCKER / MAJOR / MINOR |

## 4. Quotes (verbatim; only if the quotes box was ticked)
- "…" (P07)

## 5. Demo observation (only if run)
First click (where they went first):
Stalls over 60 s:  screen | at which second | what they said
"NOT a submission" line read?  yes / no / partial
Export caveat read?  yes / no / partial
Reached the export control unaided?  yes / no — if no, where they stopped
Help given: what, at which second
Demo not run because:

## 6. Close
One thing they would change:
Would they pay, and for what (their words):
Referral: offered / declined / situation suggested (no name):

## 7. Coding
Friction tags (from the vocabulary, max 3 per finding):
Steps affected:
Assistable: YES / POLICY / NO
Severity mix: __ BLOCKER, __ MAJOR, __ MINOR
New tag needed? propose the word and a one-line definition here:

## 8. Findings lines (derived, anonymised — these may outlive the recording)
- F-01 …
```

## Friction tags — the fixed vocabulary

Every friction line in §3 gets at least one tag from this table. A tag that is
not here is proposed in §7 and either adopted (and added here in the same
change) or rejected with a reason. Silent synonyms are how a frequency table
becomes fiction.

| Tag | Means | Sounds like |
|---|---|---|
| `FIND` | Could not find the right page, office, counter or form | "I didn't know where to start", "someone told me to go to the tehsil" |
| `UNDERSTAND` | Did not know what was required, or what a label meant | "what does self-attested mean", "it asked for father's name — which father's name" |
| `PROVE` | Did not have the document, or had the wrong form of it | "the bank statement was three months old", "they wanted it on letterhead" |
| `FILL` | Made an error filling the form, or could not fill a field | "it wouldn't accept my date of birth in that format" |
| `PAY` | Fee, payment method, or an unexpected charge | "the challan had to be paid at a different counter" |
| `WAIT` | Processing or queue time | "I went back after three weeks and it was still pending" |
| `RETRY` | Rejection, re-upload, or a correction cycle | "they rejected it and I had to start again" |
| `TRAVEL` | A physical trip that was necessary | "two trips to the office, one to the notary" |
| `LANGUAGE` | English-only text where the person reads Hindi | "I couldn't read what the error said" |
| `DEVICE` | Phone vs desktop, scan or photo quality, connectivity | "the photo was too big to upload" |
| `TRUST` | Fear of sharing, of being tracked, or of the agent seeing everything | "I didn't want to upload Aadhaar to a website" |

## Steps — the second axis

`NEED` (deciding they needed it) · `FIND` · `GATHER` (collecting documents) ·
`FILL` · `UPLOAD` · `PAY` · `SUBMIT` · `TRACK` · `COLLECT` · `CORRECT`

Every friction line sits on a step. This is what turns "the process is hard"
into "seven of twenty participants lost a day at GATHER, none at SUBMIT".

## Who did the work

`SELF` · `AGENT` (paid) · `FAMILY` (unpaid help) · `OFFICE` (staff filled it) ·
`MIXED`

Record who did what at each step, not one label for the whole attempt. The
interesting finding is usually a mixed case: self-applied, but an agent for the
upload.

## Assistable — the third axis

| Value | Meaning | Consequence |
|---|---|---|
| `YES` | RINAVI could remove this inside Assist-only — comprehension, preparation, evidence checking, tracking guidance | Goes to the product queue |
| `POLICY` | Removing it needs submission, portal access, credentials, or a legal change | Goes to the owner as a scope question, never to the code queue |
| `NO` | Department behaviour, fee policy, statutory waiting time | Goes to the findings report as context, not as a product task |

`POLICY` is the honest label for the largest category of citizen pain, and the
one a founder is most tempted to relabel as `YES`. Apply it strictly: if the
fix requires RINAVI to press submit, it is `POLICY`.

## Severity

| Value | Anchor |
|---|---|
| `BLOCKER` | The attempt stopped here and did not resume within the study period — they gave up, or paid someone to finish |
| `MAJOR` | Cost a retry, an extra trip, or more than a day of elapsed time |
| `MINOR` | Annoyance or confusion that did not change the path |

Severity is assigned from the consequence, not the tone. An angry participant
with a minor annoyance is `MINOR`; a calm participant who quietly stopped is
`BLOCKER`.

## Worked example (illustrative, not a real session)

| Their words | Step | Who | Tags | Assistable | Severity |
|---|---|---|---|---|---|
| "I filled everything and then it said the father's name didn't match my Aadhaar, so I had to go back to the notary." | `FILL` → `CORRECT` | `SELF`, notary for the affidavit | `FILL`, `RETRY`, `PROVE` | `YES` | `MAJOR` |
| "I gave it to a man near the office; he charged 500 and did it in two days." | `SUBMIT` | `AGENT` | `TRAVEL`, `TRUST` | `POLICY` | `BLOCKER` |

The first row becomes a product requirement (consistency checks between a
field and the document that carries it). The second becomes a business-model
question, not a backlog item.

## Writing rules

1. **Same day, within 24 hours.** After that, write "reconstructed later" at the
   top and treat the note as weak evidence.
2. **Quotes stay verbatim** between quotation marks. A paraphrase is marked
   `[paraphrase]`.
3. **Names out, codes in.** Replace a name inside a quote with `[name]`. The
   quote still works; the person is gone.
4. **A story that identifies someone is not retold — it is summarised as a
   category.** "A school clerk in outer Delhi" is fine; "the clerk at the
   Rohini school who helped with the scholarship" is not.
5. **Never write down** an Aadhaar number, an application number, an exact
   income, a phone number, an address, an employer, a password or an OTP. If one
   slips in, redact it immediately and note that you did.
6. **Do not revise a note after the rollup has used it.** Append a dated
   correction instead.

## The limitation to state in the report

One coder, no second reader, no inter-rater reliability. The frequency table is
one person's consistent judgement, not a measured instrument. Say that in the
findings report rather than implying otherwise — it is the first question a
reviewer will ask, and volunteering it costs nothing.

