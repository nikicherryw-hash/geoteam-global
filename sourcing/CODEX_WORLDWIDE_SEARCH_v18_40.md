# Codex: GeoTeam Global Worldwide Sourcing v18.40

**ACTIVE_PRODUCT:** `GEOTEAM_GLOBAL`. **Do not mix with SKS/Archivist/other tenants.**

## Mission

Complete, test and publish a **broad worldwide source-discovery search** within today's GeoTeam Global release workflow. Before any real supplier APIs are licensed, this build should cover legitimate public company catalogs, specialist industrial stores, regional B2B portals and wholesale marketplaces through curated, click-through internet search.

**Repository**: https://github.com/nikicherryw-hash/geoteam-global

**Work branch**: `geoteam-v18-40-worldwide-discovery`

**Target Firebase project** (owner confirmed via console screenshots): `geoteam-global` (currently Spark/no-cost).

**Existing production Firebase**: Hosting release `ce3aeb`, functions `rfq` and `ticker` (`us-central1`, red `Function deployment failed` warning). Do NOT modify, redeploy, delete or migrate these during this task. Do NOT switch to Blaze. Do NOT touch DNS, existing Hosting default site, mail, or any SKS resources.

## Examine first

- `preview-v18-7/sourcing.html` and `preview-v18-7/global-source-finder.js`
- `preview-v18-7/data/sources.v1.json`
- `sourcing/foundation/source_registry.v1.json`
- `sourcing/foundation/validate_sources.py`
- `sourcing/backend/functions/` and its `test/` suite
- `sourcing/WORLDWIDE_DISCOVERY_v18_40.md`
- `sourcing/deploy/publish_directory_cloud_shell.sh`
- Git tree, release commits and existing deployment state.

## Requirements: broad search BEFORE supplier APIs

1. Inventory **134 registered candidates**: **131 product-related sources**, 3 logistics references, with no duplicates. Covers Russia/CIS, Europe, Türkiye, China, India, Korea, Japan, Indonesia/Malaysia/ASEAN, North and Latin America, Middle East/Africa, Australia/Oceania.
2. Confirm/review live website availability and category relevance in batches; do not represent stale or inaccessible sites as verified. Mark unreachable or rights-restricted candidates clearly.
3. Route by exact part query, OEM/brand hints, source specialization and **supplier market region**, not by destination alone. Unknown part numbers must still get broad general-B2B candidates, not fake matches.
4. Support RU/EN/TR, mobile/iPhone Safari, keyboard accessibility.
5. Support user-click outbound searches on **Google, Bing, Yandex and Baidu**, both open-web and `site:vendor.domain` modes, with exact query preserved. Do not fan out to hundreds of websites, scrape, defeat bot blocks, harvest logins or automate RFQ sends without explicit rights and approval.
6. Show every eligible directory candidate through incremental pagination (12 initially + show more). Do not cap the matching universe at 13.
7. The result must say clearly **SOURCE_DISCOVERY_ONLY**, with no invented inventory, prices, delivery terms, supplier verification or stock updates. Country/territory appearance does not prove export eligibility.
8. Existing RFQ manual draft/copy/email/WhatsApp user-initiated actions must remain intact.
9. Update and run Node 22 tests, Python validator, browser E2E and mobile checks. Detect/fix misleading statuses and dead links; do not silently hide test failures.
10. Keep the future Firebase HTTP adapter separate and disabled/un-deployed. An API being documented does not imply we have permission to use it.

## Firebase publication — strictly isolated

A dedicated additional Hosting site in project `geoteam-global` is proposed: `geoteam-sourcing-20261029` (provided it is available). Never replace default Hosting site `geoteam-global`. Inspect the complete Firebase state and actual CLI account/project first. Backup/read the current default site release metadata for readback only.

Review `sourcing/deploy/publish_directory_cloud_shell.sh` and correct any mistakes, **especially its pinned commit SHA, scope, source count and deployment target**, before use. Running stale v18.39 scripts is prohibited. Deploy only the separate Hosting target (static assets; no Functions/Blaze). Stage preview, test, then deploy ONLY if owner authorized and access is available. The owner has authorized publication of the independent search site, but not any production replacement, billing, DNS, Functions or database changes.

After deployment, independently retrieve `sourcing.html`, `global-source-finder.js`, `data/sources.v1.json`, `release.json`, and verify full content/commit/readback and browser functionality. If the release cannot be completed, mark BLOCKED, provide one safe executable Cloud Shell command and the precise blocker.

## Next phase (PREPARE ONLY; no external integrations without approval)

Design source adapters and onboarding documentation for licensed data feeds (Mouser, DigiKey, TrustedParts, Nexar/Octopart, Farnell/element14, Arrow, aviation platforms, manufacturer partners), selective authorized indexing, supplier identity verification, MPN exact matching, provenance/time of price, exchange rates, logistics/tariffs, RFQ tracking, rate limits, legal reuse rights, trade/export compliance and independent GeoTeam DB.

Do not subscribe, buy, contact vendors, enable billable APIs, create new third-party projects, install Supabase or deploy backend. External providers and APIs require explicit authorization and commercial/technical review.

## Mandatory final report

- ProductID, files changed, source counts by region/category, QA checks and exact Node/Python/E2E test commands/results.
- What is VERIFIED vs UNVERIFIED vs NOT RUN vs BLOCKED.
- Git commit/PR link and deployed public URL **only if verified**.
- Firebase project/site, source version, readback and unchanged existing production release.
- Source candidate reachability checks and known limitations.
- Risks, rollback and exact implementation status.
- Never claim live pricing, all-web scraping, production search, or supplier API connections unless real independent evidence exists.
