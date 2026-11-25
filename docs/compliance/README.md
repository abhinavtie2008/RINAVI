# Compliance documents — what is public and what is not

**Status:** repository note, not a compliance artefact. **Updated:** 2026-11-24,
against `main` @ `71b5023`.

This folder lives in a public repository. Everything here is written to be safe
to publish: it describes a **synthetic, assist-only** phase A pilot and carries
no participant data, no credentials and no exploit-level detail. The split below
is deliberate, and the rules at the end keep it that way.

## Public by design

| File | Why it is safe to publish |
|---|---|
| `reviewer-brief.md` | The ask, Q1–Q3, the eight accepted risks and the decision box. No reviewer name or contact details. |
| `pilot-plan.md` | How the synthetic session runs; roles are named by role, not person. |
| `pilot-runbook.md` | The operator's steps: topology and the dev-sign-in constraint, the pre-session gate, the between-session wipe, support, incidents, pack re-verification. No participant data. |
| `data-map.md` | What is stored, where, and which consent purpose gates it. No real records. |
| `privacy-notice-draft.md` | Participant-facing draft; contact is a role, not a private individual. |
| `terms-draft.md` | Participant-facing draft; assist-only limits. |
| `retention-policy.md` | Deletion and retention rules for synthetic data. |
| `recording-consent.md` | Separate consent for notes and recordings, and its script. |
| `portal-permission-register.md` | A0 only: no portal access, credentials or adapter. |
| `threat-model.md` | Redacted summary of 31 threats, the controls, and the eight accepted risks with reopen triggers. |
| `wp8-pilot-readiness.md` | The authoritative compliance decision ledger. |

## Held privately, never committed

- **Detailed residual register** — the exploit-level detail behind
  `threat-model.md` §6, including the publication-history note. Given to the
  reviewer directly; it is not a repository file.
- **Legal-review PDF pack** — contains the register. A point-in-time artefact,
  generated outside the repository.
- **Reviewer identity and engagement terms** — personal data. Recorded privately
  by the pilot owner; this folder names the role only.
- **Real documents, real participant data, host names and credentials.**

## Rules

1. Nothing moves from private to public without a redaction pass, and the public
   version names the risk without the exploit.
2. A draft that becomes final, or is abandoned, gets its status line updated in
   the same change. A stale public draft is worse than no draft.
3. No individual's name or contact details in this folder — roles only. The
   reviewer, facilitator and participants are identified privately.
4. Before the first real document, re-check what stays public. The reopen
   triggers in `threat-model.md` §6 and `wp8-pilot-readiness.md` apply to
   publication too.
