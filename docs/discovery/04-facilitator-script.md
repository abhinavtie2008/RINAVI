# Facilitator script — the 45 minutes

**Status:** draft instrument, 2026-11-24. Written so that someone who has never
seen RINAVI can run a valid session with this file, 01, 03 and 05, and nothing
else. The done-when test for the kit is exactly that.

## Before the session (10 min, not counted)

- [ ] Consent form printed twice (`../compliance/recording-consent.md` §5), or
      the verbal-consent path ready on the note.
- [ ] Note template open (05), headed with the P-code, date, channel, language.
- [ ] Stopwatch or phone timer ready, face down.
- [ ] Two SPECIMEN PDFs available, and the prototype running locally. If it is
      not running, the demo is cancelled — never improvised on a live portal.
- [ ] Nothing from a previous participant on screen: no account, no browser
      history, no document list. If the previous session's account was not
      deleted, delete it now and log the delay as a hygiene miss.
- [ ] Phone silent; no notifications on the shared screen.

## The clock

| Minutes | Phase | What happens |
|---|---|---|
| 0–3 | Welcome | 01 read aloud, "any questions before we start?" |
| 3–10 | Consent | Six boxes, one at a time, signed; then the recording question for the demo only |
| 10–35 | Interview | 03 blocks A–E, in order. Protect this block |
| 35–42 | Demo, optional | Participant drives; facilitator does not click |
| 42–45 | Close | Referral ask, thank you, deletion date stated |

**If time runs short, cut the demo, never the interview.** A session with no
demo and a complete account is a valid session. A session with a demo and half
an account is not.

## 1. Welcome (0–3)

Read 01's script. Then one sentence that is not in it: *"There are no right
answers today — I'm testing the problem, not you."*

Do not describe the product before the interview. The moment you explain what
RINAVI does, the account of the attempt reorganises around it.

## 2. Consent (3–10)

Hand over the form. Read each box aloud and let them answer each one
separately — a single "yes, all fine" is not consent to six different things.

- If notes are refused: *"That's fine — I'll just listen and won't write
  anything down."* Then actually don't. The session still runs.
- If recording is refused: the demo is not recorded. Do not offer audio-only
  after a no (`recording-consent.md` §6).
- Write the deletion date on the form before the session ends, not afterwards.

## 3. Interview (10–35)

Use 03. Two facilitator habits decide whether the notes are usable:

- **Ask, then wait.** Five seconds of silence after every answer, minimum.
- **Write the exact words.** "It kept saying invalid" is not data; *"it kept
  saying the father's name doesn't match"* is.

## 4. Demo (35–42, only if consented)

### The framing sentence, verbatim

> "This is a prototype running on this laptop. It is not a government website,
> nothing you type goes anywhere, and nothing is submitted. The documents
> inside are fake specimens. I'm not going to explain it first — I'd like you
> to try to get to the point where you'd have everything ready to apply. Talk
> out loud if you can."

### Then stay quiet

- **Do not click, do not point, do not type.** If they ask what to do, answer a
  question with a question: "What would you try?"
- **A stall is the finding.** When a participant stops moving for more than 60
  seconds, or says "I don't know what this means", note the screen and the
  second, then offer exactly one sentence of help and note that you did.
- **Log the first-click path.** Where they go first is the navigation result,
  and it is usually wrong in an informative way.
- **Watch for the two lines the product depends on:** the *NOT a submission*
  notice on the draft, and the caveat on the export card. If they never read
  them, that is a comprehension finding, not a participant error.

### The route, if they ask for one

Home → sign-in (say it is a local prototype, not a real account) → the three
consents → vault upload of the two specimens → profile promotion and
confirmation → catalogue → draft, evidence, declaration → export. This is
`pilot-plan.md` §4.3; do not invent a shorter path to make the demo end well.

### If item 102 is not deployed

Record "export control not collectable" and stop the demo at the draft. Do not
simulate the screen, and do not tell the participant it exists if it does not.

## 5. Close (42–45)

- "Anything you'd have done differently if I weren't watching?" — catches
  facilitator effects.
- Referral ask (03 §E).
- Say the deletion date out loud: *"The recording, if we made one, goes on
  [date]."*
- Thank them and stop the clock.

## Stop conditions

Straight from `pilot-plan.md` §8, and none of them is negotiable:

| Situation | Do |
|---|---|
| A real document is offered or shown | Stop, ask them to put it away, do not upload. If it was already captured, delete that part in front of them and record the incident in `docs/evaluation/` with no personal data |
| Portal credentials, OTP or CAPTCHA come up | Refuse, explain the Assist-only boundary in one sentence, record the request as product feedback |
| Consent is withdrawn mid-session | Stop recording immediately, delete what they ask for, end the session kindly. Note the time |
| They ask you to fill their real application | "I can't — this is research and I'm not allowed to handle real documents." Then offer the interview |
| They become distressed | Stop. Nothing in this session is worth a bad hour. Record only that it stopped |

## Remote sessions

ADR-0004 makes the platform remote-first, so some sessions will be over video.

- Send 01 the day before, and confirm the participant has a device that can
  join and, for the demo, see a shared screen.
- **Share your screen, not theirs.** Their desktop may contain real documents.
- Announce when recording starts and stops, on the recording itself.
- If the call drops: wait two minutes, then email; reschedule rather than
  finish by phone. A half-session is not counted in the 20.
- Ask them to close other windows before the demo — a notifications banner with
  a real name is a data incident waiting to happen.

## Facilitator hygiene

1. Never explain a screen before it is tried. Explained confusion is
   unmeasurable.
2. Never defend the product. "That's a good point" and write it down.
3. Never fill silence with your own hypothesis.
4. Never run two sessions back to back without writing the first note. The
   second will overwrite the first in memory.
5. Never let the demo run past 42 minutes because it is going well. The note
   written at 23:00 is worth less than the one written at 16:00.

