# Worldwide Discovery v18.40 — continuation of v18.39

**ProductID:** GEOTEAM_GLOBAL. **Status:** PREPARED, staging only.
**Date:** 2026-10-29. No change to live Firebase project or website.

## Expanded coverage

Candidate source registry: **134 records**, comprising **131 product-related catalogs, marketplaces, manufacturers and B2B directories** plus **3 logistics references**. Added 90 candidates with geo scope across Russia/CIS, China, India, Korea, Japan, ASEAN, Türkiye, Europe, North and Latin America, Middle East/Africa, Australia/Oceania.

**These are website links, NOT live integrations, crawled databases, licensed catalogs, verified offers or active API connectors.** The label `CANDIDATE_NOT_LIVE_VERIFIED` is deliberately attached to candidates. A site may require login, local language, a corporate account, or be inaccessible in certain countries. No provider catalog was copied into GeoTeam.

### Search UX

- Category auto-detection by brand / exact part number / key industry terms (explicit category override available).
- Region selection with a worldwide default; worldwide mode includes sources across all registered regions.
- Four outbound search engines: Google, Bing, Yandex, Baidu; links include exact entered query and optionally `site:provider.domain`.
- No requests to those engines until user clicks. No background browser crawling.
- Results sorted by source category and regional relevance, **not by verified SKU availability**.
- The previous `slice(0,13)` limitation has been removed. Results display 12 cards at a time with a `Show more sources` control.
- RU, EN, TR labels. Supplier search destination is not automatically sent to any search engine.
- All prices, inventory and logistics fields remain UNVERIFIED / absent.

The HTTP adapter remains PREPARED ONLY. It accepts `region` and validates it, but Cloud Functions has not been deployed. Actual cross-site aggregation of listings, real supplier offers and landed costs are Phase 2 after official permissions.

### Engineering acceptance

- Check 134 registry entries, 131 non-logistics sources; no duplicate IDs, invalid URL protocols, non-GeoTeam tenants, or accidental `enabled:true` entries.
- Test exact Siemens, Schneider, ABB, Irtysh, aviation, HERMLE and manufacturing-to-drawing classification.
- Test each geographical region is represented and results are paginated rather than truncated.
- Verify Google/Bing/Yandex/Baidu links and no automatic cross-origin search requests.
- Verify all RU/EN/TR labels, iPhone Safari display, DOM/XSS safety, RFQ draft/copy links.
- Audit candidate URLs for actual reachability and current terms; mark invalid providers DISABLED before production. **Current provider reachability review is incomplete.**
- Perform `node --test` on real Node 22 runtime, Firebase Hosting emulator, browser E2E tests and HTTP readback on independent preview site.
- Do not upgrade Blaze, deploy Cloud Functions, alter default Hosting, SKS, mail services or DNS.
- Preserve immutable source commit and rollback plan when producing deployment artifact.

**Testing status:** isolated Code Mode tests cover 21 unit/API contract cases and all pass; runtime Node process, Firebase release and real Safari visual tests NOT RUN. Codex should reproduce with actual Node 22 and Playwright/iOS Safari (when available).

**Source evidence spot-checks:** elec.ru, tradekorea.com, inaexport.id, gisp.gov.ru/emetall, industrysearch.com.au, misumi-ec.com, etc. Remaining candidates still require human/site verification and permission review.

**Release:** see `sourcing/deploy/publish_directory_cloud_shell.sh` AFTER it is updated and revalidated for this v18.40 source commit. Previous v18.39 release scripts are not valid for v18.40.
