# docs

Two kinds of content live in this folder.

**Project documents**: `architecture/`, `compliance/`, `evaluation/`, `handbook/` and `planning/`.

**A static demo of the web UI**: the `*.html` pages and `assets/`. It is a second,
browser-only implementation of the citizen flow (consent, vault, profile, applications,
locker, packet) for GitHub Pages. There is no server and no build step. Everything a
visitor adds stays in their own `localStorage`, and it is meant for synthetic data only.
It is not the product; `apps/web` is. What it stores and what the host can see are
recorded in `compliance/data-map.md` §10.

## Run the demo locally

```bash
python3 -m http.server -d docs 8000   # then open http://localhost:8000/
```

## Keep it in step with the code

The demo copies or ports three things. `scripts/check_demo_sync.mjs` runs in CI and in
`scripts/check.sh`, and fails when they drift.

| Demo file | Mirrors |
|---|---|
| `assets/js/pack.js` (service and pack data) | `catalog/services/**/service.json` and `versions/<latest>/service_pack.json`, copied exactly |
| `assets/js/extract.js` (extraction rules) | `backend/app/modules/documents/extraction.py`, a hand port checked against it on a set of fixtures |
| `assets/js/core.js` (consent, drafts, locker) | the backend modules, mirrored by hand and **not** checked by the script |

When the check fails, update the demo file it names. When you change `core.js`, read the
matching backend route first: for example, completing a draft is gated on
`applications.preparation` alone, and the demo does the same.

## Publishing with GitHub Pages

Every link in the demo is relative, so it works wherever the folder is served.

- With Pages set to build from `main` and the repository root, the demo is at
  `/RINAVI/docs/`, and the README remains the site's home page.
- To make the demo the site's home page, set Pages to build from `main` and `/docs`.
  Then `404.html` and `.nojekyll` take effect, and the README is no longer the home page.
  (Under the root setting they do nothing, because GitHub only reads them from the
  folder it publishes.)

## Fonts

Bricolage Grotesque and Hanken Grotesk are bundled in `assets/fonts/` as Latin subsets,
so pages make no third-party requests. Both are licensed under the SIL Open Font
License 1.1; the licence texts sit next to the files.
