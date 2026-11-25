# ADR-0004: Pilot hosting ladder and the remote-first platform direction

**Status:** Accepted (2026-11-24, founder decision) · **Execution trigger:** the qualified legal review signing off item 83 — nothing in this ADR is provisioned before that

## Decision

RINAVI's product direction is a **platform usable by people anywhere in India, joining remotely on their own devices**. Sessions are therefore not assumed to be face-to-face with the operator. The pilot must rehearse that shape, and hosting follows a ladder of increasing commitment, each rung gated:

| Rung | What runs | Precondition | Cost |
|---|---|---|---|
| 1. Now (pre-review) | Nothing is reachable from the internet. Development, tests, and the compose stack stay local. | — | ₹0 |
| 2. First hosted state | **Cloudflare Tunnel** on the operator's machine during supervised sessions — remote participants, HTTPS from the first click, a stable URL | Item 83 signed off; the privacy notice (§7) and `data-map.md` §1 updated in the same change to name the tunnel carrier and "reachable over the internet" | ₹0 |
| 3. First always-on home | **Oracle Cloud Always Free** VM (India region: Mumbai/Hyderabad) running the compose stack, app + PostgreSQL 16 + reverse proxy with read/send timeouts at least as long as the web client's 30 s request / 120 s upload bounds (closes wp8 gap 7) | Rung 2 used in practice and its fragility (operator machine awake, residential uplink) observed; same disclosure updates | ₹0, with recorded caveats: card required, ARM capacity availability, idle-instance reclamation |
| 4. Platform scale | Paid VM or managed PaaS. A managed provider becomes acceptable here **because** a nationwide platform has processor relationships by design; the choice is made through a processor review, not in passing | Real-data launch; `data-map.md` §1 "Data Processor: None" rewritten; DPDP §8 security practices; children's-data handling (verifiable parental consent) decided for the service set | Paid |

The **pilot runs at rung 2**: remote supervised sessions (video call + screen share or equivalent), participants on their own devices from their own locations, synthetic SPECIMEN documents only. In-person sessions remain permitted but are no longer the assumed shape.

The backup/restore drill (checklist A7) runs against whichever rung is live when the drill happens, and its target is recorded in the drill output.

## Rationale

- The platform direction is the product's stated goal; a pilot that only exercises same-room use would rehearse the wrong experience. Remote supervision preserves the pilot's safeguards (facilitator present, synthetic data, small cohort) while matching the destination.
- Free tiers are sufficient to reach rung 3 and are chosen over a paid VM deliberately: cost is not the bottleneck for a two-person project, and a free-tier failure is itself evidence for the rung-4 decision.
- Option (c) — managed PaaS — was rejected **for rungs 2–3 only**, not in principle: it adds a data processor, which the pilot's "no outside company processes anything" stance forbids and the legal review has not scoped. At platform scale that stance is expected to change through the processor review, not in passing.
- Hosting of any kind — free or paid, tunnel or VM — is gated by item 83. Deciding the ladder now costs nothing and leaves nothing to improvise the day the review signs off.

## Consequences

- **ADR-0002 amendment:** the PostgreSQL production cutover target is the rung-3 (then rung-4) host; the cutover itself stays deferred per ADR-0002 and happens on the rung live at the time.
- **`docs/compliance/`:** the privacy notice §7 ("single computer in [city]"), `data-map.md` §1 (§ "Data Processor: None") and §8 (hosting/location), and `threat-model.md` §7 (hosting, TLS, proxy listed as out of scope) must each be updated in the same change that activates rung 2 — never after.
- **The WP2 reviewer brief gains two platform-horizon questions:** (1) processor selection at rung 4; (2) **children's data** — income certificates for scholarships imply minors, so DPDP verifiable parental consent and the ban on tracking/targeted advertising at children are in scope from the first real-data day if that service set stays.
- **wp8-pilot-readiness gap 7** (no reverse proxy) closes at rung 3, not rung 2 — a tunnel is not a proxy with configurable timeouts; the gap stays open and owned until then.
- **Pilot ops (B4):** the runbook gains a "remote supervised session" section — pre-session device check, what the facilitator shares, what happens on disconnect — written before rung 2 activates.
- **Reopen:** a change of platform ambition, a free-tier policy change (Oracle reclamation, Cloudflare terms), or a legal-review finding that blocks tunneling specifically.

## Related

- ADR-0002 (databases), ADR-0003 (module scope — `execution`/`integrations` remain post-pilot; a platform ambition does not move them earlier)
- Checklist items 53 (cutover), 64 (encryption at rest), 68 (retention sweeps), 83 (legal gate), 84 (pilot operations)
