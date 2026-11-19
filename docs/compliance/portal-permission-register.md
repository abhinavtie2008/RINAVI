# Portal-permission register — draft

**Status:** draft for the WP2 legal/privacy review, and the precondition WP10
(checklist item 87) names before any browser extension or portal adapter is
built. **Date:** 2026-11-19, against `main` @ `45c63d7`.
**Companion to:** `data-map.md` (what RINAVI stores), `threat-model.md` (what
can go wrong), `pilot-plan.md` §6 (what the pilot does not collect).
**Authority:** `wp8-pilot-readiness.md` stays authoritative for compliance
decisions. This is not legal advice, and nothing here grants permission from any
government body — no such permission exists or has been requested.

## 1. What this register is for

RINAVI sits next to government portals. "Permission" is used in three different
senses in this project, and they are easy to confuse:

| Sense | Who grants it | Where it is recorded |
|---|---|---|
| **Citizen authorisation** — may RINAVI use this person's data for this purpose? | The citizen, per purpose, revocable | `consent_records`; four fixed purposes |
| **Portal permission** — do the portal's own terms allow this kind of access (automated login, form fill, scraping, submission)? | The portal operator, in its terms of use | **This file** — currently unverified for every portal (§8) |
| **Statutory basis** — what does the DPDP Act or a sector rule require? | Law, interpreted by the qualified reviewer | Readiness ledger; not this file |

The register exists so that a future decision to automate anything is made
against a written record of what each portal allows, not against an assumption
that "it is a public website". **V1 requests no portal permission at all**, and
that is the point of every row below.

## 2. Access levels

Every portal entry names one of four levels. The level is what the *system* may
do, independent of what the citizen may ask for.

| Level | Name | What the software may do | Status in V1 |
|---|---|---|---|
| **A0** | None | No network connection to the portal, no stored credential, no stored session, no automated read | **Every portal, today** |
| **A1** | Citizen-driven copy | Produce a packet the citizen copies or retypes into the portal themselves, in their own browser session | **Today's product**: `GET /applications/drafts/{id}/export` and the case packet |
| **A2** | Assisted fill | A browser extension or adapter prefills fields in the citizen's already-signed-in browser tab | **Not built**; needs an approved register, a security review and item 87 |
| **A3** | Automated submission | The system signs in and files the application | **Out of scope**; would need written authorisation from the operator and a new ADR (item 90) |

A1 is not a portal access level in the technical sense: no request leaves the
RINAVI deployment. It is listed because it is the highest level V1 reaches, and
because "we only produce text the citizen pastes" is the claim a reviewer will
want to test.

## 3. The register

| ID | Portal / service | Operator | Official address | Level today | What the system actually does | Portal permission required for this level |
|---|---|---|---|---|---|---|
| R-01 | e-District Delhi — Income Certificate | Revenue Department, Government of NCT of Delhi (e-District programme) | `https://edistrict.delhigovt.nic.in/` | **A0** for the portal; the citizen acts at **A1** using RINAVI's text | Nothing. RINAVI never opens a connection to this host. The citizen registers with their own mobile number, fills the form, declares and submits in their own browser | None. Reading a public page and quoting a service's steps into a pack is the only contact, and it happened at authoring time, not at runtime |
| R-02 | Revenue Department, GNCTD — Income Certificate information page | Revenue Department, GNCTD | `https://revenue.delhi.gov.in/revenue/income-certificate` | **A0** | Cited as an official source in `catalog/services/edistrict/income-certificate/service.json`. No runtime access | None for citation; confirm the page may be quoted and linked (§8) |
| R-03 | UIDAI / Aadhaar | UIDAI | — | **A0** | No Aadhaar number is stored outside `extracted_fields`, and none is promoted, drafted, exported or packed (A1, item 35) | None; Aadhaar is entered only at the portal by the citizen |
| R-04 | DigiLocker | MeitY / NeGD | — | **A0** | Not integrated. No OAuth client, no fetcher | **Would require partner approval** — item 89, blocked on it |
| R-05 | National Scholarship Portal (NSP) | Ministry of Education | — | **A0** | Not in the catalog; no pack exists | Not applicable until a pack exists — item 86 |
| R-06 | CPGRAMS | DARPG | — | **A0** | Not in the catalog; no pack exists | Not applicable until a pack exists — item 86 |
| R-07 | Any other state e-District portal | State governments | — | **A0** | Out of scope: one pack, one geography | A new entry here, and its own review, before any pack is added |

The catalog has exactly one service (`delhi-income-certificate`, pack `1.0.0`).
That is why R-01 is the only row with a real "what happens" column: the register
can be short because the product is narrow.

## 4. What RINAVI does with a portal, step by step

For R-01, in the order the citizen experiences it:

1. RINAVI shows the pack's `official_channel_steps` — register on the portal,
   choose the department and service, fill the form, upload self-attested
   documents, review and submit, save the application number.
2. The citizen builds a draft and exports it. The export carries a
   `not_a_submission_notice` and a "NOT a submission" line in the text.
3. The citizen opens the portal in their own browser, signs in with their own
   mobile number and OTP, and types or pastes the values.
4. The citizen may come back and record what happened: status, reference
   number, acknowledgement number, deadline, outcome notes.

Steps 1 and 2 are offline. Step 3 involves no RINAVI component: there is no
extension, no injected script, no bookmarklet, no proxy. Step 4 stores what the
citizen tells us, typed by hand.

**Reference numbers are citizen-entered data, never fetched.** `application_cases.reference_number`
and `acknowledgement_number` come from a request body the citizen fills
(`locker` module); no code parses a portal page or calls a portal endpoint to
obtain them, and the app tells the citizen it cannot see what happened on the
portal (`apps/web/src/features/locker/CaseDetail.tsx`).

## 5. Prohibitions, and what makes each one structural

Each row is enforced by absence of code, not by a policy sentence. That is the
distinction the review needs: an absent field cannot leak.

| # | Prohibition | Why it is structural | Evidence |
|---|---|---|---|
| P1 | Never stores a portal password | No password, PIN or secret field exists in any schema, and no `credentials` column holds a secret — `credentials` stores a passkey **public** key and sign counter only | `backend/migrations/versions/`, `identity/models.py` |
| P2 | Never asks for or relays an OTP | No OTP field, no SMS integration, no mobile number collected at all | `data-map.md` §9; `pilot-plan.md` §6 |
| P3 | Never solves or bypasses a CAPTCHA | No CAPTCHA handling, no OCR of challenge images, no headless browser dependency | `pyproject.toml` has no browser-automation package; `package.json` has no scraper |
| P4 | Never opens a portal session | The only cookie the system sets is `rinavi_session`; no portal host appears in any cookie, redirect or fetch | `identity/routes.py::set_cookie`; `core/config.py::cors_origins` |
| P5 | Never submits an application or declaration | No `execution` module, no outbound HTTP client in the runtime dependency set, no submission route; the declaration is a local boolean the citizen sets | ADR-0003; `pyproject.toml` (runtime deps only); `applications/routes.py` |
| P6 | Never scrapes a portal | No HTML parser for portal pages, no crawling, no scheduled fetch; nothing runs on a timer at all | No scheduler or worker package exists (readiness ledger item 1/6) |
| P7 | Never bulk-collects other people's applications | Every query is scoped by the session's `user_id`; there is no admin or staff role, and no cross-account read route | `data-map.md` §6; `tests/integration/test_locker_api.py`, `test_documents_api.py` |
| P8 | Never stores an Aadhaar number outside the parsed document | Aadhaar is filtered from profile reads, promotions, draft snapshots, values, validation, export, packets and the `/fields` response | `core/privacy.py`, PR #52; residual in `data-map.md` §3.3 |

P5 deserves a note, because it is the claim the whole register rests on. The
backend has no HTTP client in its runtime dependencies — `httpx` appears only in
the `dev` extra, where it drives the test client. Adding any portal integration
therefore requires a new dependency, a new module and a new register entry, which
is three reviewable changes rather than one quiet one.

## 6. Citizen authorisation, per portal

The four purposes are purpose-scoped to *data*, not to a portal
(`data-map.md` §4). At A0 no per-portal consent is needed, because nothing is
sent anywhere and the portal never sees RINAVI:

| Portal | Data RINAVI gives the portal | Consent needed today | Consent that would be needed before A2 |
|---|---|---|---|
| R-01 e-District Delhi | Nothing. The citizen types the values themselves | `applications.preparation` to build the draft, `locker.tracking` to record the case | A new, explicit, per-portal authorisation — not an extension of the existing four — plus a security review and an updated privacy notice |
| Any other portal | Nothing | N/A | The same, recorded here first |

Before any A2 work, the register must additionally answer: what exactly the
extension reads from the page, whether it writes into the page or only the
clipboard, how the citizen revokes it, and what is stored from the portal's DOM.
None of that is designed, so none of it is claimed.

## 7. Change control

A change to this file is required, and must be reviewed, before:

1. **Adding a portal** — a new row, with operator, address, level and permission
   basis. Adding a service pack is not a portal decision; adding runtime contact
   with a portal is.
2. **Raising a level** — A0 → A1 is a product change, A1 → A2 needs the register,
   a security review and item 87, A2 → A3 needs written operator authorisation
   and an ADR.
3. **Storing anything new about a portal** — a portal identifier, session, token,
   cookie, screenshot or receipt.
4. **Quoting portal text** — the pack's guidance is derived from the official
   sources; a wording change is a content change with a legal edge (§8).

The register is versioned with the repo. A change lands in the same pull request
as the code it authorises, so the two cannot drift.

## 8. Open items for the reviewer

These are the questions this file cannot answer from inside the repository. They
are listed here rather than guessed, and every one of them is a task for the
qualified review:

1. **Terms of use, per portal.** No portal's terms have been read for this
   draft. The review must check, for R-01 and R-02: whether automated access is
   addressed at all; whether an assistant that prepares text for the citizen is
   permitted, prohibited or silent; and whether the terms bind a third-party
   tool rather than the citizen.
2. **Naming and affiliation.** The pack names the Revenue Department and links
   the portal. The README and privacy notice disclaim affiliation. The review
   should confirm the disclaimers are sufficient for the way the portal is named
   and whether any logo or mark is used (none is).
3. **Quoting guidance.** `official_channel_steps` paraphrases the official
   process. Confirm that quoting process steps is acceptable, as opposed to
   copying substantive form text or instructions verbatim.
4. **Mobile-number registration.** The portal requires a mobile number to
   register. RINAVI does not collect one and must not start doing so without a
   recorded purpose and an entry here.
5. **Recording a portal reference number.** The citizen types it; RINAVI stores
   it as case data. Confirm that storing a reference number the citizen supplies
   is covered by `locker.tracking`.
6. **A2 preconditions.** If a guided-fill extension is ever proposed, this
   register must be approved *first* — item 87 makes it a hard trigger — and the
   extension needs its own security review (Manifest V3, restricted permissions,
   no remote code).

## 9. Not covered

- Any state other than Delhi, and any service other than the income certificate.
- DigiLocker (item 89) and portal integrations (ADR-0003, `integrations` module).
- Portal-side conduct by the citizen: what they paste, whether they paste
  correctly, and what the portal does with it. RINAVI is not in that path.
- Whether the citizen is eligible. The portal decides; RINAVI stays advisory
  (ADR-0003, readiness "Found after WP7" §1).

## 10. Version history

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-11-19 | First draft: seven portal rows, all A0; prohibitions P1–P8 with their structural evidence; six open items for the reviewer |
