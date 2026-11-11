# ADR-0001: Modular monolith backend

**Status:** Accepted (2026-11-11)

## Decision

Build the backend as a single FastAPI application with internal modules
(`identity`, `consent`, `vault`, `documents`, `profile`, `catalog`,
`applications`, `execution`, `locker`, `audit`, `integrations`) sharing one
database, one API entry point, and one deployment unit.

## Rationale

One application keeps cross-module invariants (source-linked profile,
versioned templates, consent-before-processing) enforceable in-process
without distributed transactions. Module boundaries stay testable because
each module exposes a contract and is replaced independently.

## Consequences

- No per-module services or databases in V1.
- Discipline is required to keep modules from reaching into each other's
  internals; module contracts live in the master build plan.
- Splitting a module out later is possible but not planned for V1.
