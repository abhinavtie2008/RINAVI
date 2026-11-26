# Candidate packs

Draft service packs live here. Nothing in this folder is served by the app, copied
into the demo, or offered to a citizen.

## Why this folder is invisible

The loader reads one root, declared in `backend/app/modules/catalog/loader.py`:

    CATALOG_ROOT = <repo>/catalog/services

`list_services()`, `get_service()` and the pack lookups read only
`catalog/services/**`. A pack under `catalog/candidates/` therefore cannot appear in
the app, cannot be read by a draft, and cannot drift into `docs/assets/js/pack.js`.
Invisibility is a property of the code path, not a convention someone has to
remember.

## What a candidate contains

    catalog/candidates/<group>/<service>/
    ├── service.json
    └── versions/<version>/service_pack.json

`<group>` mirrors the grouping used under `catalog/services/` — today that is
`edistrict` — and `<service>` is the service folder. The files use the same schema as
a published service: `service.json` for the metadata, a versioned pack under
`versions/`. A candidate is a proposal, not a promise: it may be wrong, incomplete,
or withdrawn.

## Promotion

A candidate becomes a service only when both of these happen:

1. the owner records the decision in `docs/planning/v1-checklist.md` item 86 (the
   second-service evidence gate); and
2. the promotion pull request moves the folder into `catalog/services/...` and
   updates the demo mirror in `docs/assets/js/pack.js` in the same change.

A green test publishes nothing, and merging a candidate publishes nothing. The
recorded decision is the only thing that promotes it.

## `last_verified` is not available yet

Do not add `last_verified` to a candidate. That optional key arrives with the loader
work recorded as D5; until then the dossier carries the retrieval date.

## Status

The first candidate is Delhi's domicile certificate. Its dossier (S2) precedes its
pack (S3), and neither is published.
