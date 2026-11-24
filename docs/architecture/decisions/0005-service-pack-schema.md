# ADR-0005: Service-pack schema grows by optional additive keys

**Status:** Accepted (2026-11-24, founder decision)

## Decision

The service pack (`catalog/services/**/versions/**/service_pack.json`) grows its
service knowledge through **optional additive keys in the existing file**,
not through a separate knowledge file:

- `rejection_reasons` — common reasons this service's applications are rejected, each with the citizen-facing remedy
- `correction_path` — how to correct or reapply after a rejection, and any window that applies
- `renewal` — whether and how the certificate is renewed, and when
- `complaint_channels` — official grievance channels (portal, CPGRAMS, department), as citable links
- `last_verified` — the date the pack's guidance was last checked against the official source, with the source cited

Rules:

1. Every key is **optional**. A pack without them is valid and behaves exactly as today.
2. The loader validates the **shape** of a key when present (typed, link fields must be URLs, dates must be ISO) and ignores nothing silently: a malformed present key is a `CatalogError`, not a degraded page.
3. The UI degrades cleanly when a key is absent — the service page simply does not show the section.
4. Adding or filling these keys is a **minor** version bump (`1.0.0 → 1.1.0`). Adding a *form field* or changing checklist semantics stays a **major** bump, as before.
5. **Stored snapshots are never migrated.** Drafts and cases keep the `pack_version` and `template_snapshot` they were created with; the loader and UI must tolerate a snapshot without the new keys, indefinitely.
6. `docs/assets/js/pack.js` mirrors the whole file, including the new keys; `check_demo_sync` enforces it exactly as it does today.

## Rationale

The repository's demonstrated failure mode is two files that must change together
drifting apart — the reason `check_demo_sync` exists. A separate `knowledge.json`
doubles that surface (a second loader path, a second demo mirror, a second guard
scope) to buy a separation nothing currently needs. If the knowledge volume ever
justifies it — an order of magnitude of services with rich content — migrating
from this shape to a split file is mechanical: the loader splits, the keys move,
the version bumps again. Starting additive is reversible; starting split adds
permanent overhead.

The citizen-facing behaviour is identical under both options, so the choice is
maintainability-only, and (a) is the shape that lets knowledge grow fastest
without touching form logic.

## Consequences

- **Sequencing (two PRs, strictly ordered, no shared file):**
  1. YooExE adds the optional keys, loader validation, and tests (`fix(catalog): optional service-knowledge keys`).
  2. The owner fills the income-certificate pack from official sources and mirrors `pack.js` (checklist B7).
- A malformed-but-present knowledge key fails loudly (`CatalogError`) at load, not as a broken page.
- The `last_verified` stamp surfaces per service; a staleness rule (e.g. "review after N days") is a UI/ops consideration, deliberately **not** mandated here — it can be added without schema change.
- Old snapshots never grow the new keys and never need to; nothing reads them for the new sections.
- Reopen: knowledge volume or multi-author editing justifying a split file; a key family that turns out to need form-level semantics (it would then be a major bump, not an additive one).

## Related

- ADR-0003 (module scope — the compliance resolver stays post-pilot; these keys are descriptive, not decisions)
- Checklist item 45 (resolver stays advisory — knowledge keys describe what the portal does, they do not decide eligibility)
- `scripts/check_demo_sync.mjs` (mirror enforcement, unchanged in scope)
