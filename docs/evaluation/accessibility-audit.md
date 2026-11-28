# Accessibility audit (WP11)

Date: 28 November 2026
Scope: `apps/web` on `main` at `e50cd14`, plus the API it calls on `http://localhost:8000`.
Data: synthetic only. One dev-sign-in account (`audit@example.com`), two synthetic PDFs
generated in-process (income evidence, identity evidence), one draft, one completed case
(`SYNTH-REF-0001`). No real documents and no portal contact of any kind.

## Method

| Tool | Version | How it ran |
|---|---|---|
| axe-core | 4.14.0 | Injected into the running app in the preview browser, `axe.run(document)` restricted to `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22a`, `wcag22aa` |
| Lighthouse | 13.6.0 | Headless Chrome (`--headless=new`), `--only-categories=accessibility`, against a signed-in session |
| Keyboard | — | Tab traversal in the preview browser, `document.activeElement` and its computed `outline` after each Tab |

Both colour schemes were run because `globals.css` changes `--background` under
`prefers-color-scheme: dark`. Lighthouse always runs light, so it is the light column only.

`/applications/<id>`, `/locker/<id>` and `/locker/<id>/packet` were audited with the synthetic
draft and case above, so they render real field values, evidence lists, a journal and a packet
rather than empty states.

## Results

`n` is the number of axe violation nodes. Lighthouse scores are the accessibility category.

| Route | axe (light) | axe (dark) | Lighthouse | `<main>` | `<h1>` |
|---|---|---|---|---|---|
| `/` | 0 | 0 | 100 | yes | **no** |
| `/catalog` | 0 | 1 | 98 | **no** | **no** |
| `/applications` | 0 | 2 | 98 | **no** | **no** |
| `/locker` | 0 | 1 | 98 | **no** | **no** |
| `/vault` | 0 | 2 | — | yes | yes |
| `/profile` | 0 | 12 | — | yes | yes |
| `/consent` | 0 | 5 | — | yes | yes |
| `/account` | 0 | 6 | — | yes | yes |
| `/applications/<draft>` | 0 | 9 | — | **no** | yes |
| `/locker/<case>` | 0 | 7 | — | **no** | yes |
| `/locker/<case>/packet` | 0 | 13 | — | **no** | yes |

Light mode: no axe violations on any of the eleven routes. Every failure below is either
dark-mode-only or a structural issue axe does not score.

## Findings

### F1 — Dark mode makes text unreadable (blocker)

- **Where:** every route, worst on `/locker/<case>/packet` (13 nodes), `/profile` (12),
  `/applications/<draft>` (9), `/locker/<case>` (7), `/account` (6), `/consent` (5).
- **WCAG 2.2:** 1.4.3 Contrast (Minimum), AA. Required 4.5:1 for body text.
- **Evidence:** `axe color-contrast` reports `#737373` on `#0a0a0a` = **4.17:1**
  (`text-neutral-500`, 12px) and `#525252` on `#0a0a0a` = **2.53:1** (`text-neutral-600`, 14px).
  Example targets: `.text-xs.text-neutral-500` on `/profile` value rows, `p[data-testid="account-user"]`,
  `.text-neutral-600` in `/consent`.
- **Cause:** `apps/web/src/app/globals.css` swaps `--background` to `#0a0a0a` for
  `prefers-color-scheme: dark`, but every component uses fixed light-theme neutrals
  (`text-neutral-500/600`, `border-neutral-200`, `bg-amber-50`, `text-green-800`, …). Dark-mode
  users get near-black text on a near-black page. This is not a subtle contrast miss; it is the
  whole palette inverted against invisible text.
- **Fix (one file):** remove the `@media (prefers-color-scheme: dark)` block in
  `globals.css` so the app keeps the palette it is designed for, **or** add dark variants to every
  component. The first is a one-line change and the only one that can be verified today; the
  second is a design task. Do not leave both in place.

### F2 — No main landmark on six routes (serious)

- **Where:** `/catalog`, `/applications`, `/locker`, `/applications/<draft>`, `/locker/<case>`,
  `/locker/<case>/packet`.
- **WCAG 2.2:** 1.3.1 Info and Relationships (A); 2.4.1 Bypass Blocks (A).
- **Evidence:** Lighthouse `landmark-one-main` fails on `/catalog`, `/applications`, `/locker`
  (score 98 each). `document.querySelector("main")` is `null` on all six.
- **Cause:** `ServicesPage`, `ApplicationsPage`, `CasesPage`, `DraftDetail`, `CaseDetail` and
  `PacketPage` return a bare `<div>`; the five routes that do pass wrap their component in
  `<main>` in the route file (`app/vault/page.tsx`, `app/profile/page.tsx`, etc.).
- **Fix:** wrap the root element of those six components in `<main>`, matching the other routes.

### F3 — Four routes have no `<h1>` (moderate)

- **Where:** `/`, `/catalog`, `/applications`, `/locker`.
- **WCAG 2.2:** 1.3.1 Info and Relationships (A); 2.4.6 Headings and Labels (AA).
- **Evidence:** `document.querySelectorAll("h1").length === 0` on all four. `/locker` has no
  heading element at all; `/applications` and `/catalog` start at list content, `/` starts at a
  `<p>` banner. A screen-reader user has no page title to jump to.
- **Cause:** `app/page.tsx` renders `AppBanner` (a paragraph) and a nav; `ServicesPage` and
  `ApplicationsPage` render lists without a heading; `CasesPage` likewise.
- **Fix:** one `<h1>` per route — "Services", "Applications", "Case locker", and a real heading
  for the banner copy on `/`.

### F4 — Status messages are not announced (serious)

- **Where:** every feature that renders an error paragraph:
  `SignInArea`, `VaultPage`, `ConsentPage`, `ProfilePage`, `DraftDetail`, `CaseDetail`,
  `PacketPage`, `ApplicationsPage`, `ServicesPage`, `AccountPage`.
- **WCAG 2.2:** 4.1.3 Status Messages (AA).
- **Evidence:** `grep -r 'aria-live|role="alert"' apps/web/src` returns **0 matches**. Errors are
  rendered as `<p data-testid="…-error">` after an async failure; nothing is announced, so a
  screen-reader user who triggers "Could not save the correction." hears nothing. Loading states
  (`data-testid="*-loading"`) are equally silent and carry no `aria-busy`.
- **Fix:** give each error paragraph `role="alert"` (or wrap the region in `aria-live="polite"`),
  and set `aria-busy` on the container while a request is in flight.

### F5 — No skip link, nav repeated on inner pages (moderate)

- **Where:** all routes that render `SiteNav` (`/vault`, `/profile`, `/consent`, `/account`,
  `/locker/<case>`, `/locker/<case>/packet`) plus the home nav.
- **WCAG 2.2:** 2.4.1 Bypass Blocks (A).
- **Evidence:** `document.querySelector('a[href^="#main"], a[href^="#content"]')` is `null`.
  Tabbing from the top reaches five nav links before page content on every inner page.
- **Fix:** add a visually-hidden "Skip to content" link at the top of `SiteNav` (or the layout)
  targeting `#main`, and give the `<main>` an `id`.

### F6 — Focus indicator is the browser default only (minor)

- **Where:** every interactive element.
- **WCAG 2.2:** 2.4.7 Focus Visible (AA) **passes**; 2.4.13 Focus Appearance (AAA) fails.
- **Evidence:** after Tab on `/`, the focused button's computed outline is
  `auto 0.8px rgb(229, 151, 0)` — the UA default, with `box-shadow: none`. It is visible, but thin
  and low-contrast against the page.
- **Fix:** add a `focus-visible` ring (for example `focus-visible:outline-2 focus-visible:outline-offset-2`)
  to the shared button/link classes if the project wants AAA.

## What passed

- Every form control has a programmatic label (`label[for]` or `aria-label`): sign-in email,
  upload file input, draft field inputs, correction input, case reference/acknowledgement/outcome
  inputs, deadline date. axe `label` rule passes on all pages.
- Tab order follows DOM order; no positive `tabindex` anywhere.
- `<html lang="en">`, one `<title>` per document (all identical — see the A5 PR #131, not merged).
- Detail pages have a sensible heading outline (`h1` service name → `h2` sections → `h3` checklist
  groups).
- No dialogs, modals, carousels, autoplaying media or animated transitions, so there is no focus
  trap or motion to report.
- No images other than the Next.js dev-tools button, which is development-only.
- Light mode: zero axe violations on all eleven routes; Lighthouse 100/98/98/98.

## What this audit does not cover

- **No screen-reader pass.** NVDA and VoiceOver both need a human at the machine; I could not run
  one and will not claim I did. The announcements in F4 are therefore inferred from the DOM, not
  heard.
- **No complete keyboard journey.** The upload step needs the OS file picker, which cannot be
  driven from the preview browser. I verified tab order, focus visibility and reachability of the
  upload control, but did not complete upload → promote → draft → packet → case using the
  keyboard alone.
- **No zoom/reflow (1.4.10), text spacing (1.4.12), mobile-width or reduced-motion pass.**
  Lighthouse ran at its default desktop viewport only.
- **No print check** of `/locker/<id>/packet`, which has print-specific classes.
- **Lighthouse was not run on** `/vault`, `/profile`, `/consent`, `/account`, the draft, the case
  or the packet — the four primary routes plus axe cover them.
- **Findings are not fixed in this PR.** F1 is a blocker; the fix belongs in the next PR.

## Verdict against the recorded bar

The bar recorded for this work package is **WCAG 2.2 AA on the four primary pages plus full
keyboard traversal**. On today's `main`:

- Light mode on the four primary pages: **at AA** by axe, except the missing `<main>` landmark
  (F2) and the missing `<h1>`s (F3).
- Dark mode: **not at AA on any page** (F1).
- Status messages (F4) fail AA everywhere an async error can appear.
- Full keyboard traversal: partly verified, see above.

So the project is **not yet able to claim WCAG 2.2 AA**. F1 is the blocker; F2–F5 are the rest of
the gap.
