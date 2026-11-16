# ADR-0003: V1 module scope

**Status:** Accepted (2026-11-16, founder decision)

## Decision

V1 ships the nine modules implemented under `backend/app/modules`:
`identity`, `consent`, `vault`, `documents`, `profile`, `catalog`,
`applications`, `locker` and `audit`.

`execution` and `integrations` are post-pilot work. They are not stubbed in
V1, and no API contract promises them. ADR-0001 remains the target
architecture; this ADR records what V1 actually delivers.

The compliance resolver is also post-pilot. V1 is Assist-only: RINAVI
prepares drafts and evidence checks, but the official portal decides
eligibility and RINAVI does not submit applications. A future resolver can be
added as a read-only projection over the existing pack snapshots, profile
values, document links and validation results; it does not require a schema
change for the basic readiness check.

## Rationale

- V1 is Assist-only, so submission automation (`execution`) and external
  portal integrations (`integrations`) have no V1 behaviour to implement.
- Empty modules create maintenance and review overhead without delivering a
  workflow.
- Keeping the delivered module set explicit stops the readiness record and
  the architecture document from disagreeing about "9 of 11".
- The resolver is a policy decision, not a data-model commitment. Deferring
  it keeps the pilot conservative while preserving an additive path.

## Consequences

- The module coverage gap is recorded as V1 scope, not as missing work.
- Adding `execution`, `integrations` or the resolver later needs a new ADR or
  an update to this one, plus its own tests and consent review.
- The readiness record links here instead of treating the two absent modules
  as an unexplained gap.
- V1 does not claim eligibility decisions. Any future readiness output must
  stay advisory and keep the official portal authoritative.
