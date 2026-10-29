# GeoTeam Global — Universal Sourcing v18.41
**ACTIVE_PRODUCT:** GEOTEAM_GLOBAL. **Status:** PREPARED, NOT DEPLOYED.
**Date:** 2026-10-29.

## Product decision
Every user request is worldwide by default. No user country, IP, VPN location, browser locale or selected supplier region shall constrain coverage. Delivery location is kept as a logistics input only. The entire existing sourcing page and manual RFQ workflow remain; region/search-engine selection fields are replaced with a worldwide coverage statement. Four open-web engines (Google/Bing/Yandex/Baidu) remain as click-through choices **within the results**.

## Source catalogue (candidate directory, not scraped index)
- **223** distinct registered sites, of which **220** product-related and **3** logistics.
- New channels include private classifieds, retail stores, regional marketplaces, used industrial machinery, insolvency/surplus auction houses, industrial catalogues, manufacturers, aviation and electronics distributors.
- Representative names: Avito, Ozon, Wildberries, Yandex Market, FarPost; Sahibinden, Trendyol, letgo, Makinecim, n11; European Kleinanzeigen/Leboncoin/Subito/Gumtree, eBay, Amazon; Asia 1688, Taobao, JD, Coupang, Yahoo Auctions Japan; US Craigslist, Surplus Record, Machinio, EquipNet, Kitmondo, BidSpotter; OLX Brasil/Mercado Livre; Gumtree South Africa/Jiji; Trade Me/Machines4U.
- All `integration_status` values remain `NOT_CONNECTED`, all `enabled:false`, all `verification_status:CANDIDATE_NOT_LIVE_VERIFIED`. Source inclusion is not proof of availability, contract, serviceability, right to crawl or verified authenticity.

## Correct results
1. Normalize exact OEM and part number; multilingual terms and brand names are hints, not stock matches.
2. Rank all registered sources by product specialization, without geographic exclusion. Display in pages of 12; user can show more until all relevant candidates are visible.
3. **Do not** automatically fan out 220 direct requests; static Firebase Hosting cannot lawfully/reliably bypass cross-site CORS/login/robots restrictions. Outbound searches only occur on user click.
4. Site-restricted external engine links and open web search links send the query only when clicked.
5. A listing is `UNVERIFIED` until provider evidence is obtained through an authorized API/feed or explicit supplier confirmation. A source-directory entry alone must never be treated as an actual listing.
6. For future live-feed integration, `listing-status.js` labels sold/ended/expired auctions as `INACTIVE`, old observations as `STALE`, and current provider listings as `OBSERVED_ACTIVE` but still **not purchasable** until seller confirmation. Every price, condition, quantity, freight, origin and date needs provenance.
7. Include safe independent verification: identity, counterfeit risk, item condition, original documentation, export/territory restrictions, customs and import rules. An auction's ended state must not silently persist in live-stock results.

## Phased production architecture
**Now (Spark-capable):** static worldwide discovery and RFQ drafts on isolated Firebase Hosting site. No provider APIs. No backend invocation necessary.

**Next phase with approvals:** provider adapters for publicly documented, licensed product search APIs; seller/stock confirmation, controlled refresh, rate limits, source provenance, normalized listing database and deduplication. Prefer exact MPN over fuzzy similarity. Separate GeoTeam DB only after ownership and hosting preflight.

**Later:** asynchronous targeted provider fanout with request budgets + audit, end-user request tracking, landed-cost estimator (customs/HS/origin/Incoterms/shipping), seller outreach and verified quotation workflow. Never require unlimited parallel web crawling or claim every site can be automatically accessed.

## QA + release gates
- 223 source records / 220 search sources; no duplicate IDs/URLs.
- 21 routing/API contract checks + 6 listing freshness tests, current test suite.
- `python3 sourcing/foundation/validate_sources.py` and `cd sourcing/backend/functions && node --test` must PASS in actual runtime before deploy.
- Validate link protocols, 3 language variants, HTML/JS syntax, real browser and mobile Safari, legal/privacy/RFQ regressions. Sample international, used, private and aviation searches.
- No production deploy without separate Firebase Hosting site preflight and confirmed site ID; no Cloud Functions or SKU API integration. Preserve original GeoTeam Hosting/Functions.
- Pin source revision, verify files, upload to isolated site, HTTP readback and a real browser smoke test. Rollback only independent site if release fails.
- Record `VERIFIED`, `NOT RUN`, `BLOCKED` rather than claiming completeness.

## Known limits
- Candidate website availability and permissions have not been validated exhaustively.
- Results are *search directions*, not automatic live price/inventory. No finished auctions can be filtered from search-engine results without authorized listing data and evidence.
- Full automatic distributed web scanning cannot be delivered on static Firebase Spark; it requires an explicitly authorized backend, provider APIs/search licensing and measured infrastructure.
