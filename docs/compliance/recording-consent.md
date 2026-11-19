# Recording and notes consent — draft

**Status:** draft for the WP2 legal/privacy review. **Date:** 2026-11-19.
Separate from the product consent purposes: this covers the **research
recording**, not the app's use of data. Not legal advice.

**Why it is separate.** A participant can use the prototype and refuse to be
recorded; the pilot still works. Bundling the two would make the recording feel
mandatory, and the interview is more useful when it is not.

## 1. What is recorded, and what is not

| Item | Offered | Default |
|---|---|---|
| Handwritten or typed notes | Always | On |
| Audio recording | Optional | Off |
| Screen recording of the session | Optional | Off |
| Video of the participant | Optional | Off |
| Direct quotes in a write-up, anonymised | Optional | Off |
| Screenshots of a blocker | Optional | Off |

Never recorded: anything the participant types into a real government site, any
real document, any password, OTP or CAPTCHA, and any part of the session the
participant asks to pause.

## 2. What the recording is for

Only two things: understanding where the product fails, and writing an internal
findings note. Not marketing, not a public testimonial, not training data, not
shared with any third party. If a quote is used in an internal write-up it is
attributed as "participant 4", never by name, and only if the participant ticked
that box.

## 3. Where it lives and for how long

- Kept in the pilot folder on the facilitator's machine, outside the RINAVI
  system, not uploaded anywhere.
- Deleted **90 days after the session**, or at pilot close if that is sooner.
- The deletion date is written on the session record so it can be checked.
- Notes derived from a recording (a findings line, an anonymised quote) may be
  kept without the recording, because they contain no personal data.

## 4. Withdrawal

The participant can withdraw at any time — during the session, or afterwards by
email — and the recording and notes about them are deleted within
**[7] days**, with the deletion confirmed in writing. Withdrawal does not affect
their participation, and no reason is needed. Withdrawal after a finding has
been written up removes the recording and any quote; the anonymised finding
itself stays, because it no longer identifies anyone.

## 5. Consent form

> **RINAVI pilot — recording and notes**
>
> Participant: ______________________  Session date: ____________
> Facilitator: ______________________  Participant code: P___
>
> I have read, or had read to me, the section above. I understand that:
>
> - taking part in the pilot does not depend on saying yes to any of this;
> - I can withdraw at any time, and my recording and notes will be deleted
>   within 7 days;
> - recordings are kept for 90 days at most, on one machine, and are not shared.
>
> Please tick what you agree to:
>
> - [ ] Notes taken during the session
> - [ ] Audio recording
> - [ ] Screen recording
> - [ ] Video of me
> - [ ] Anonymised quotes in internal write-ups
> - [ ] Screenshots of the app when something breaks
>
> Signature (or verbal consent, recorded by the facilitator):
> ______________________________________  Date: ____________
>
> Facilitator confirms the choices above were read back to the participant:
> ______________________________________  Date: ____________
>
> Deletion due by: ____________  Deleted on: ____________

Two copies: one to the participant, one in the pilot folder. If consent is
given verbally, the facilitator reads the form aloud, records the answer in the
session note, and does not start recording until the answer is on the note.

## 6. Facilitator script

Read this before the session, after the product consent, and before any
recording starts:

> "This part is separate from the app. I'd like to take notes, and if you're
> comfortable, record the session, so I can remember exactly where things went
> wrong. You can say no to any of it and still take part. You can also ask me to
> stop recording at any point, or to delete it afterwards — just email me. The
> recording stays on this laptop and is deleted within 90 days. Is that okay?
> Which parts are you comfortable with?"

If the answer is no to everything:

> "That's completely fine — I'll just watch and won't write anything down. Let's
> start."

Do not persuade, do not re-ask, and do not record "just the audio" after a no.

## 7. If something sensitive is captured by accident

Stop the recording immediately. If a real document, a real Aadhaar number or a
portal screen was captured, delete that segment in front of the participant,
record the incident in `docs/evaluation/` **without personal data**, and tell
them what was deleted. This mirrors the stop conditions in `pilot-plan.md` §8.

## 8. Open decisions for the review

- Whether the 90-day period should match the pilot close-out date exactly, so
  there is one deletion event rather than two.
- Whether screen recording is worth the risk at all, given screenshots may be
  enough and are easier to redact.
- Who holds the pilot folder if the facilitator is unavailable — a named second
  person should, before the first session.
