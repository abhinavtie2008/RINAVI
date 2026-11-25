# Recruitment and screening

**Status:** draft instrument, 2026-11-24. Recruitment copy must be approved by
the owner before it is posted anywhere, and must not promise approval, faster
processing or government affiliation (`../compliance/pilot-plan.md` §3).

## Who is being recruited

People who have **tried** to get a Delhi income certificate in the last two
years. The unit of evidence is a real attempt, not an opinion about apps.

| Group | Definition | Target (min unless marked) | Why |
|---|---|---|---|
| Self-applied | They filled and submitted it themselves, at least once | 6 | The product's core user; also the group that can say where the form itself broke |
| Agent-assisted | An agent, cybercafé or broker did it, paid or unpaid | 6 | The comparison that decides whether RINAVI's value is comprehension or convenience |
| Outside the personal network | Recruited through an NGO, college or group, not a friend-of-a-friend | 5 | A network-only sample measures the founder's friends |
| Semi-urban or peri-urban | Outside core south/central Delhi | 4 | The remote-first platform claim (ADR-0004) needs at least some non-metro evidence |
| Abandoned before applying | Decided they needed it, never applied | max 3 | Separates "the process is hard" from "the requirement is unclear" |
| Insider | Works in a Revenue Department office or a CSC | max 2, counted separately | Useful, but never counted in the 20 — a staff account is not a citizen account |

Also aim for at least five women and at least four participants who say they
are more comfortable in Hindi than English. Neither is a quota to fake: record
what the sample actually was, and say so in the findings.

**Total: 20 minimum, 30 maximum.** Item 82 says 20–30; below 20 the scorecard
has no denominator, above 30 the marginal session rarely changes the ranking.

## Recruitment copy

Short version, for a WhatsApp group or a noticeboard:

> **Did you apply for an income certificate in the last two years? (45 min,
> Delhi or video)**
>
> I'm researching how the income-certificate process actually goes — what
> worked, what didn't, how many trips it took. I'm building a small prototype
> for the preparation step and want to understand the problem before I decide
> what to build next.
>
> - 45 minutes. In person in Delhi, or over a video call.
> - Don't bring anything. No documents, no papers.
> - You don't need to have succeeded — an attempt that failed is just as
>   useful.
> - This is research, not a service. Taking part does not get you a
>   certificate, faster processing, or any connection to a government office.
>   RINAVI is independent and not affiliated with or endorsed by any
>   government department.
> - If we look at the prototype, its documents are clearly marked fake
>   specimens. Nothing is submitted anywhere.
>
> Reply with a time that suits you.

Longer version for an NGO or college contact: add the two sentences below, and
nothing else — every extra sentence is a promise someone will hold you to.

> I'm speaking to 20–30 people so the answers are comparable, and I'm
> deliberately including people who used an agent as well as people who filled
> the form themselves. Notes stay on my laptop, names never appear in anything
> I write, and recordings are deleted within 90 days.

## Screening script

Ask these six, in this order, and stop as soon as one answer disqualifies.

| # | Question | Disqualifies when |
|---|---|---|
| 1 | "Have you applied for, or tried to apply for, an income certificate in the last two years?" | No, and never considered it → not a primary participant |
| 2 | "Did you finish the application, or did it stop somewhere?" | — (either is useful; record which) |
| 3 | "Who filled the form — you, someone in your family, or an agent?" | — (this assigns the group) |
| 4 | "Are you willing to talk for about 45 minutes about how it went?" | No → stop |
| 5 | "Would you rather do this in Hindi or English?" | Hindi, and the facilitator is not fluent → note it and book only if a fluent facilitator is available; otherwise record as a language finding |
| 6 | "Do you want RINAVI to process a real application for you during this?" | Yes → excluded, and explain the Assist-only boundary in one sentence |

Do not screen for income, caste, age or documents. You do not need any of it,
and asking creates a record you then have to protect.

## The recruitment log

Kept privately, one row per contact, never in this repository:

| Field | Example |
|---|---|
| Contact ref | C04 |
| Channel | college noticeboard |
| Screened on | 2026-11-27 |
| Eligible | yes |
| Group | agent-assisted |
| Language preference | Hindi |
| Session booked | P07, 2026-12-01 11:00, video |
| Contact detail | *(private sheet, not this file)* |

The log is how the mix in the table above is actually held. Check it after every
five sessions: whichever row is furthest behind is who you recruit next, even if
the next willing person is another self-applied friend.

## What to do when someone wants help with their real application

Refuse in one sentence, without moralising: "I can't help with a real
application — this is research, and I'm not allowed to handle real documents."
Then, if they are willing, interview them about the attempt itself. This is the
`pilot-plan.md` §8 stop condition, and the request itself is a finding: record
it as *demand for assistance beyond preparation* in the rollup, no names.

