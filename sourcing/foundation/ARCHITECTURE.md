# GeoTeam Global — Global Sourcing Foundation

**Status:** PREPARED / architecture only. **ProductID:** GEOTEAM_GLOBAL.
**Date:** 2026-10-29. **Base UI:** v18.37. **Production:** UNCHANGED.
The sources in `source_registry.v1.json` are **candidates**, not active provider
integrations, supplier contracts, live offers, available stock or verified prices.

## VERIFIED repository state

The preview repository contains static HTML, translations and RFQ draft UI.
`preview-v18-7/sourcing.html` requests:
- `GET /api/sourcing/suggest?q=...&lang=...`
- `GET /api/sourcing/search?query=...&quantity=...&destination=...`

No backend implementation of those endpoints is present in this repository.
The preview explicitly disables live supplier search on githack/GitHub Pages.
The RFQ buttons open a user-controlled draft: no remote supplier requests are sent.
The homepage globe and source page remain untouched by this foundation package.
Actual production hosting, VPS sizing, database, domains and contracts are **UNVERIFIED**.

## Product architecture / independent infrastructure

```text
Site RU/EN/TR
  -> same-origin authenticated /api/sourcing/*
  -> query normalization & technical matching (manufacturer + MPN + revision)
  -> compliance eligibility (country / party / HS / ECCN / end use)
  -> source router (type, location, permissions, API quota, latency budget)
  -> PostgreSQL local index and evidence cache
  -> bounded concurrent, approved provider adapters
  -> normalize / deduplicate / confidence labels / provider provenance
  -> staged results (catalogue, potential source, live listing, confirmed quote)
  -> optional landed-cost calculator and RFQ tracking
  -> customer-facing result / human review / explicit supplier RFQ approval
```

Key nonfunctional rules: do not fan out every search to all sources; route by
product category, region, part number, permitted destinations and provider budget.
Preserve exact OEM part IDs and revision suffixes. Never merge substitutes
without evidence/technical review. No stale supplier price labelled live.
Preserve source URL, observed_at, currency, unit, MOQ, condition, quantity basis,
documentation, seller identity, allowed destinations, and agreement/license limits.

### Proposed canonical entities (separate GeoTeam database/schema)

1. `sources`: registered endpoints, terms status, priority, quota, connection.
2. `manufacturers`, `manufacturer_aliases`: names and authoritative codes.
3. `parts`, `part_aliases`: manufacturer + **exact MPN** + revision + category.
4. `suppliers`, `supplier_verifications`: organization and evidence of authorization.
5. `listings`, `offer_observations`: provenance, date, price/qty/UOM/MOQ/condition.
6. `search_requests`, `search_runs`, `connector_events`: trace and audit.
7. `rfqs`, `rfq_lines`, `supplier_replies`: immutable request history, send gate.
8. `shipping_rates`, `landed_cost_estimates`: carrier source, HS, origin and destination.
9. `customer_quotes`: commercial pricing, markup policy, currency, validity, status.
10. `access_events`, `retention_policies`: privacy, security, evidence and rights.

Never reuse SKS/SCS production tables, tenants, accounts, secrets or services by
assumption. A separate managed PostgreSQL on **the confirmed GeoTeam host**
is preferable if infrastructure permits; otherwise assess existing stack before
selecting the database and queue implementation.

## Search state and UX

- `REFERENCE_HINT`: local normalized maker/MPN suggestion, not stock.
- `SOURCE_DISCOVERED`: a relevant vendor/catalog exists, no inventory guarantee.
- `LISTING_OBSERVED`: licensed vendor evidence with timestamp.
- `SUPPLIER_CONFIRMED`: supplier responded with specific quantity and lead time.
- `QUOTATION_READY`: business-confirmed quote with full landed-cost assumptions.
- `RESTRICTED/HOLD`: trade/end-use/compliance gate; no automatic routing.

The API should expose `request_id`, `status`, `results[]`, `sources_checked`,
`sources_skipped`, `checked_at` and `warnings[]`.
A detailed result should include seller and product evidence, quote validity,
freight and customs assumptions. If unavailable, show `ASK_FOR_QUOTE` instead
of fabricating inventory, pricing or shipping estimates.

## Source policy

`OFFICIAL_API`, `PARTNER_API`, `ACCOUNT_API` and `EARLY_ACCESS_API`
mean *published API exists*, not that GeoTeam is authorized to use it.
`DIRECTORY_RESEARCH` means search/contact manually or through explicitly
licensed access; do **not** automate private login or scraping by assumption.
Every provider has `enabled:false`, `integration_status:NOT_CONNECTED`,
`rights_status:NOT_REVIEWED`. No API keys, accounts or secrets stored here.

Different API families carry different commercial and data reuse restrictions.
Examples: Mouser public API has published rate limits; PartsBase and Locatory
require commercial access; Alibaba Open Platform requires approval and scopes;
DHL rate/landed-cost uses account credentials and has contract restrictions.
Supplier outreach and actual orders require explicit owner authorization.

## Request dispatch and budget

1. Recognize exact brand/MPN and category; reject invalid or ambiguous
   substitutions. Query local source index first.
2. Filter sources by permissions, region, category and destination; exclude
   disabled/restricted sources. Apply provider-specific timeouts, queue budget,
   jittered backoff, rate limiting and circuit breakers.
3. For authorized live providers, fetch relevant current data in parallel up to a
   bounded concurrency limit; persist provenance and update rolling cache.
4. Deduplicate listings by provider listing ID; group equivalent offers by
   exact manufacturer/MPN/revision, never by approximate text alone.
5. Return verified/observed candidate records and asynchronous enrichment
   updates. Convert unconfirmed or made-to-drawing requests to a human RFQ queue.

### Logistics / landed-cost calculation

A cost is meaningful only after determining shipment origin, destination,
weights/dimensions, declared value, HS classification, origin country, trade
restrictions, Incoterms, carrier service, customs assumptions and FX timestamp.
Estimate: supplier cost + origin pickup + export handling + international freight
+ insurance + applicable import duties/taxes + customs broker + destination
last mile + GeoTeam commercial terms. Preserve the components and unknowns.
Some carriers offer rating APIs but not for every route or freight class.
Automated estimates **must not** override compliance and supplier validation.

### AI and semantic models

Phase 1 is deterministic by MPN and manufacturer, with PostgreSQL indices,
aliases and category rules. Phase 2 may add optional **local** multilingual
query classification, extraction of BOM lines and semantic candidate discovery.
AI output cannot certify OEM authenticity, interchangeable revisions, export
compliance, actual stock or prices. No external AI or paid cloud model is
authorized by this document. `AMAI` denotes no chosen supplier integration;
identify the exact service and its API before adding an adapter.

## Phases and acceptance gates

| Phase | Deliverable | Verification gate |
| --- | --- | --- |
| 0 | Hosting/server, DNS, code, legal/data-source rights audit | Read-only infra snapshot |
| 1 | Independent DB schema, seed registry, part normalization and status API | migrations/unit/API/rollback |
| 2 | Source router, cache and 3-5 approved APIs | genuine credentials, real returned data, quota QA |
| 3 | Aviation/industrial directory + RFQ source channels | manual/partner evidence, no-send controls |
| 4 | Logistics & destination pricing | account rates, customs logic review, landed-cost test cases |
| 5 | Customer request history and monitored workers | auth, privacy, webhooks, retry, E2E, load |
| 6 | Expanded geographic coverage, optional local AI | evidence-based recall/precision + cost audit |

**Pilot criteria (targets, not test results):** 100 curated real MPN/BOM queries,
including aviation, automation, discontinued components, manufacturing requests,
missing source, embargoed end-use and document uploads; zero invented offers;
no cross-tenant leakage; no unauthorized external RFQ; >=95% exact MPN matching
on the agreed pilot cases; source freshness explicit on 100% shown offers.

### Provisional infrastructure only, NOT a claim about the current server

Proof-of-concept on an isolated confirmed host: 2 vCPU / 4 GiB RAM / 40 GiB SSD.
An initial production starting point: 4 vCPU / 8 GiB RAM / 80-120 GiB SSD,
PostgreSQL, async HTTP clients, Nginx, systemd and a bounded worker.
These are **planning estimates**, not a benchmark or a requirement to migrate
providers. Match to expected QPS, parts volume, retained documents and
database query performance before allocating resources. External API quotas and
licenses will usually be the limiting factor ahead of CPU.

## Preflight required before implementation

- Identify exact **GeoTeam** VPS/hosting and services; do not assume Timeweb
  means shared SKS server.
- Identify domain/DNS and current build/deploy process, backup retention,
  database engine and restore test, existing API entrypoint and secrets vault.
- Review provider API agreements, geographic data rights, and user consent.
- Approve proof-of-concept data scope and partner API onboarding separately.
- Prepare staging/production environments and rollback before any production edit.

## Rollback and release status

Only this branch's source files added. Revert branch or omit these files to roll
back the preparation; no running service is affected. `PREPARED`, not
`DEPLOYED_VERIFIED`. No live API credentials, purchases, RFQs or server writes.
