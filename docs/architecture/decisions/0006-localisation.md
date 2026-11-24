# ADR-0006: Localisation — a Hindi comprehension layer over an English record

**Status:** Accepted (2026-11-24, founder decision)

## Decision

English stays the **language of record** for the pilot, and Hindi is added as a
**comprehension layer over it** before the first non-English session:

1. **Translated — RINAVI's own words:** the four consent purposes, a summary of
   the privacy notice, an explanation of the declaration, every validation
   message that blocks progress, and the official-channel guidance.
2. **Quoted, not translated — the government's words:** the form-field labels
   and the declaration text stay in English, with the Hindi explanation beside
   them. A Hindi substitute for a declaration is never shown, because the
   citizen ticks the wording the portal will ask for.
3. **English governs** where the two differ, and the notice says so once the
   Hindi text exists.
4. **Gate:** a Hindi-fluent reviewer signs the Hindi notice summary and the
   declaration explanation alongside the WP2 reviewer. No unreviewed Hindi
   text reaches a participant.
5. **Sequencing:** after the WP2 review lands (`B3`/`B6`) and before the first
   non-English remote session. The English pilot does not wait for it.
6. **Size of the change:** a dictionary and a language context in `apps/web`,
   scoped to the consent flow, validation and guidance — not a refactor of all
   46 source files; one bundled Devanagari face under the SIL OFL (no
   third-party requests, `data-map.md` §10); layout for strings that run 15–25%
   longer than English and for matra line-heights.
7. **Out of scope:** the service pack stays English-as-record (ADR-0005's
   knowledge keys are authored in English first), the packet stays English, and
   the static demo (an illustration, D8) is not required to carry Hindi.

## Rationale

The pilot is remote-supervised (ADR-0004), so an English-only screen means a
facilitator translating over a video call at exactly the moments comprehension
decides the outcome: what am I consenting to, what does this declaration mean,
why can I not continue. A citizen who cannot read the notice cannot be
meaningfully informed, and consent is the product's central claim.

A full translation was rejected on cost and risk. It doubles the legal corpus —
two frozen texts the reviewer must sign, plus a rule for divergence — and puts
Hindi labels over an English packet, which recreates the half-translated state:
Hindi where the citizen browses, English where they decide. Translating RINAVI's
own words and quoting the government's keeps one reviewed Hindi text, creates no
second legal instrument, and adds no new place for a mistranslation to become a
misdeclaration.

## Consequences

- `pilot-plan.md`'s Language row and §11.4's localisation exit criterion are
  updated to match.
- `reviewer-brief.md` gains the Hindi artefacts and the qualification
  requirement: the engagement needs a Hindi-fluent reader as well as the WP2
  reviewer.
- Checklist item 91 tracks the build. The sequencing rule is the gate, not a
  date.
- Once the layer is on, a screen in the comprehension scope without Hindi is a
  defect in the same way a broken trust-page promise is (D8) — partial coverage
  is the failure mode this ADR exists to prevent.
- Reopen: a second language; or a state whose portal is Hindi-only, at which
  point the pack's quoted text becomes bilingual and ADR-0005's keys carry both.
