# GeoTeam Global — Live Supplier Integrations Roadmap (PREPARED ONLY)
ProductID: GEOTEAM_GLOBAL | 2026-10-29 | Status: NO API CONNECTED / NO PAID SERVICES.

## Scope and source-of-truth boundary
The v18.42 public site is a client-side SOURCE_DISCOVERY_ONLY directory. It contains 313 vetted-for-shape candidate source records (310 product-related, 3 logistics), NOT 310 live partner integrations, live listings, or confirmed supplier offers. Do not issue any unconsented requests to supplier endpoints or reinterpret web search snippets as fresh stock.

## Candidate onboarding matrix (all not connected)
| Priority | Candidate | Value | Required authorization and evidence |
|---|---|---|---|
| P1 | Mouser | Electronics inventory/part lookup | Developer access, usage quotas, license and price/stock display rights |
| P1 | DigiKey | Distributor catalog, MPN | OAuth app registration, access grants, pricing and redistribution rights |
| P1 | TrustedParts/ECIA | Authorized distributor sourcing | Approved API, publisher rights, refresh allowances |
| P1 | Nexar/Octopart | Cross-distributor electronic parts | Subscription/access scope, permitted fields, retention license |
| P2 | Farnell/element14 | Electronics | Partner developer access, market restrictions |
| P2 | Arrow Electronics | Electronics | Partner API and rights |
| P2 | eBay Browse | Used, surplus, auction, current item state | Approved developer keys, site scopes, itemEndDate, seller/availability evidence, use restrictions |
| P2 | PartsBase/Locatory/ILS | Aviation components | Explicit commercial agreement, source access, traceability and compliance |
| P3 | Industrial marketplaces, classifieds and auctions | Equipment, used/private supply | Individual official feeds/permission; no anti-bot bypass or automated login |
| P3 | China, Korea, Japan regional platforms | Localized supply | Provider-specific developer access, legal rights, transliteration and status evidence |

## Future adapter contract (DESIGN ONLY)
- GET search requests only to approved provider APIs; authorize and isolate credentials in GeoTeam-only secrets.
- Maintain source permissions: integration_enabled, approval_ref, permitted_markets, licensed_fields, retention_limit, rate_limit, reset, currency/locale, last_success, and user-facing attribution.
- Search exact OEM/manufacturer/MPN/revision first; synonyms and translated terms only aid discovery. No unsupported equivalent substitutes.
- Persist immutable provider ID, listing ID, verified URL, observed_at, last_verified_at, end_date, seller identity/condition and provenance before rendering live offers.
- SOLD/ENDED/EXPIRED -> never available; stale/unverified -> requires seller confirmation; seller-confirmed -> preserve confirmation ID/time.
- Bound concurrency and per-provider quotas, retries with backoff, circuit breakers and idempotent dedup. No general worldwide 310-site fanout.
- Trade compliance (export controls, origin/destination/end use), seller identity/KYC, product condition and counterfeits reviewed before commercial promises.
- No cross-product data exchange with SKS, Archivist or the Timeweb server.
- Independent GeoTeam database only after architecture, hosting, backups and owner approval.
- No supplier contact, customer outreach, payment, purchase, RFQ auto-send or contract signature without explicit authority.

## Phase gates
1. P0 Static directory (this branch): source candidates and click-to-search; no live offers.
2. P1 Contract/license discovery and data/field rights reviewed by owner.
3. P2 Separate backend/API and source-by-source integration under approved spend and credentials; sandbox first.
4. P3 Verified listings with provenance and lifecycle status; QA with real data.
5. P4 Multi-line BOM, request tracking, seller confirmation, landed cost estimation with official customs/carrier data and export checks.

## Acceptance evidence (not claimed today)
- A source is LIVE_CONNECTED only after an authorized credential works, accepted API calls return genuine results, measured quotas are respected, and displayed data rights are documented.
- A listing is available only with source-provider status evidence within its TTL plus requisite seller/stock confirmation for ordering.
- Maintain regression tests, 25+ international search cases, browser Safari/Desktop checks, cost and security audits, and rollback procedures.

Status of all external integrations at time of preparation: **NOT_CONNECTED**.
