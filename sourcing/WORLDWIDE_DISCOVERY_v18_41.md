# GEOTEAM_GLOBAL — Worldwide Sourcing v18.41

**Date:** 2026-10-29. **Status:** PREPARED, preview-branch only. **Owner product:** GeoTeam Global exclusively.
**Deployment mode:** Firebase Hosting Spark static, independent second site only; no current production changes.

## Business requirement

Every query considers **the complete registered worldwide sourcing universe**, whether the customer is in
Türkiye, Malaysia, Russia, Germany, Brazil or elsewhere. Do not filter sources based on visitor IP,
VPN exit address, detected locale or delivery country. User-entered destination and optional
market preference may **change the sort order only**, never search eligibility.
Preserve the current website, RU/EN/TR translations, RFQ draft actions, header, page sections and design.

## Candidate coverage

- **269 source records total:** **266 supplier/catalog/marketplace/classified/auction/used-equipment sources**, **3 logistics references**.
- Incremental extension from v18.40: +135 public-web candidates (source file `sourcing/foundation/source_expansion_v18_41.psv`).
- Countries/areas: Russia + neighboring markets, Türkiye, Malaysia, Indonesia, China,
  Korea, Japan, Singapore, India, ASEAN, Europe, North America, Mexico, Brazil, other
  Latin American countries, Africa, Gulf/Middle East, Australia/New Zealand.
- Channels: OEM catalogs, authorized distributor candidates, general B2B directories,
  product marketplaces, **private classified ads**, **second-hand industrial equipment**,
  **industrial auctions**, surplus/old stock and technical/RFQ suppliers.
- Known site examples: Avito, Youla, Ozon, Yandex Market, Wildberries, Trendyol,
  Sahibinden, letgo, n11, Amazon regional storefronts, eBay regional storefronts,
  Kleinanzeigen, Leboncoin, OLX, Mercado Libre, Machinio, Surplex, EquipNet,
  Kitmondo, AllSurplus, Grays, Superbid, BidSpotter, MachineryTrader,
  1688, Alibaba, Goofish, tradeKorea, Jiji and many others.

**Important:** These are **candidate site URLs**, not 266 live connectors or
266 automatic provider searches. Candidate URL/site accessibility and listing search
conditions are not confirmed in bulk. Many platforms disallow unauthenticated
search/automation, return different results by locale, or require seller login.
All providers retain `enabled:false`, `integration_status:"NOT_CONNECTED"`,
`rights_status:"NOT_REVIEWED"`. No credentials, robots bypass, scraping,
commercial feeds, third-party queries, purchases or RFQ sends are introduced.

### Actual available user experience

1. User enters maker/part number, quantity, delivery location, optional category
   and optional used/new preference. Default condition **Any**.
2. Engine classifies known industrial/aviation/electronics queries and ranks
   all **266** sources, with soft region preference derived from delivery address.
3. First 12 cards intentionally mix industrial distributor, manufacturer, used,
   surplus, private classifieds, auction, B2B directory and marketplace channels.
4. All remaining cards are accessible through incremental **Show more**.
5. Links open site-restricted Google/Bing/Yandex/Baidu web searches only on
   explicit click; selected retail sites offer **native on-site search** links
   for potentially fresher data (eBay, Amazon, Avito, Trendyol).
6. Common product term multilingual variants enable searches in EN/TR/DE/ZH/JA/KO/ES
   for pumps, valves, spindles, bearings, sensors and motors, preserving the
   original OEM/MPN tokens; this is NOT certified technical translation.
7. RFQ draft/copy/email/WhatsApp remain user-confirmed. No external e-mail send
   or stock/price retrieval occurs during background search.

### Anti-stale policy — mandatory for the future ingestion layer

**Listings are not currently retrieved.** Source cards carry
`listing_state:"UNKNOWN_NOT_CHECKED"`. Never show current availability, an
auction as open, a "buy now" price, or valid stock based only on indexed search pages.

A future licensed adapter must preserve provider item ID, canonical URL,
source URL, observed_at, last_verified_at, endDate/itemEndDate, supplier status,
condition, manufacturer, exact MPN/revision, quantity, price currency,
Incoterms and end-user/ship-to eligibility.

`listingLifecycle()` provides a conservative gate for later licensed evidence:
- SOLD, ENDED (including end date in the past), UNAVAILABLE: do not present as purchasable
- UNKNOWN_UNVERIFIED: missing, stale, or unauthenticated status: RFQ/confirmation required
- ACTIVE_CONFIRMED: only source-authoritative available state, with verified timestamp
  within the configured 30-minute demo threshold and explicit provider evidence.

eBay Browse API exposes `itemEndDate` and `estimatedAvailabilityStatus`; use
the official authorized API and its licenses before treating an item as current.
Other providers may not expose listing status or restrict API integration.
For marketplace auctions also validate premium, VAT, lot location, payment,
collection deadline and suitability/quality. Industrial used equipment often
needs serial numbers, hours, technical condition, test evidence and export clearance.

## Next backend phase (planned, not deployed)

- Separate independent GeoTeam data store for sources, manufacturers,
  exact parts, aliases, provider listings, listing lifecycle, validation provenance,
  RFQ, landed costs and customer history. Never reuse SKS/Timeweb tenants.
- Connector onboarding for authorized official APIs/feeds; global query router
  dispatches only to approved and category-relevant providers with bounded
  concurrency, rate limits, retries, circuit breakers and quotas. Never fan out
  266 third-party requests on every user search.
- Real HTML search-index coverage, where allowed by provider terms, via approved
  search engine APIs; independent legal review of crawling/robots and data reuse.
- Per listing TTL, immediate end/sold suppression on verified source status,
  duplicate listing ID checks, seller fraud/KYC screening, and explicit compliance
  screening of origin, destination, product and end use.
- Compare alternative/substitute parts only with technical evidence.
- Landed-cost logic only after verified goods location, HS classification,
  shipping dimensions, Incoterms, sanctions/export restrictions and carrier data.

## Release gates / rollback

1. Audit GitHub branch, pin one immutable reviewed SHA.
2. Run `python3 sourcing/foundation/validate_sources.py` and
   `(cd sourcing/backend/functions && node --test)` in real Python/Node 22.
3. Check accessibility, language switching, accessibility, mobile Safari and RFQ.
4. Verify current Firebase project is `geoteam-global`, backup current
   default Hosting release metadata, ensure new target site ID is available.
5. Publish **only the isolated additional Hosting site** through its
   exact `hosting:sourcing` target. Do not deploy Cloud Functions or
   default production Hosting; Spark/free plan remains unchanged.
6. Verify 200/JSON for released HTML, JS, registry and release marker,
   plus 10+ real browser interactions and no false live listing claims.
7. If failed, disable/roll back the isolated new site; leave GeoTeam's
   original site and Functions unaffected.

**Current testing:** isolated V8 JS unit/API contract suite passed after v18.41
changes; real Node test process, Python validation, browser E2E, provider URL
validation at scale and Firebase HTTP readback are NOT RUN. Never report
DEPLOYED_VERIFIED until a real release is installed and checked.

## Explicit limitations

No static front-end, regardless of source count, can automatically inspect
every listing worldwide or verify current prices and auction status without
authorized provider/search API access. Site-restricted search-engine links
can include out-of-date listings; they are clearly labelled unverified.
Expansion is a durable registry foundation for the eventual real global aggregator.
