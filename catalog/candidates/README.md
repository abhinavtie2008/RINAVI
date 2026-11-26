# Candidate packs

Draft service packs live here. Nothing in this folder is served by the app, copied
into the demo, or offered to a citizen.

## Why the app does not serve this folder

The loader reads one root, declared in `backend/app/modules/catalog/loader.py`:

    CATALOG_ROOT = <repo>/catalog/services

`list_services()`, `get_service()` and the pack lookups read only
`catalog/services/**`. A pack under `catalog/candidates/` therefore cannot appear
in the app, cannot be read by a draft, and cannot reach `docs/assets/js/pack.js`
through the loader. That is a property of the code path, not a convention someone
has to remember.

Public is not the same as harmless. This repository is public on GitHub, so a
candidate is published the moment it is pushed. A candidate is a draft of a
citizen-facing document; treat it as something a stranger may already be reading.

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
recorded decision is the gate; the promotion PR is the mechanism.

## `last_verified` is not available yet

Do not add `last_verified` to a candidate. ADR-0005 (D5) makes it an optional
additive pack key rather than a separate knowledge file; it becomes usable when
YooExE's loader work lands, which is also B7's prerequisite. Until then the
session log's pack-in-use column is the record of when a pack was last confirmed,
not a field inside the file.

## Status

The first planned candidate is Delhi's domicile certificate. It is at the dossier
stage: the research that would justify a pack is not written yet, and no candidate
pack exists in this folder today. The dossier stage ends with a written account of
how the service actually behaves; the pack stage begins after that, when a
proposal is placed here for review.
