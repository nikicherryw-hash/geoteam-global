# CODEX: GeoTeam Global — WORLDWIDE SOURCING v18.41

**ACTIVE_PRODUCT:** GEOTEAM_GLOBAL. **Command:** CODE + QA + controlled independent Hosting release.
**Owner intent:** Find any potentially relevant industrial equipment or spare part
globally, irrespective of the visitor's VPN/IP, from official distributors,
manufacturer sites, wholesale and retail marketplaces, private classified ads,
industrial surplus, used machinery and worldwide auction sources.

**Repository:** https://github.com/nikicherryw-hash/geoteam-global
**Working branch:** `geoteam-v18-41-global-everywhere`.
**Existing production:** Firebase project `geoteam-global` (Spark), original Hosting
site and existing `rfq`/`ticker` functions (previous deployment errors). These
must not change. Never mix with SKS, Archivist, Timeweb or other tenants.

## 1 — Read and reconcile actual code first

Read:
- `preview-v18-7/sourcing.html`
- `preview-v18-7/global-source-finder.js`
- `preview-v18-7/data/sources.v1.json`
- `sourcing/foundation/source_registry.v1.json`
- `sourcing/foundation/source_expansion_v18_41.psv`
- `sourcing/foundation/validate_sources.py`
- `sourcing/backend/functions/`
- `sourcing/WORLDWIDE_DISCOVERY_v18_41.md`
- `sourcing/deploy/publish_directory_cloud_shell.sh`
- `sourcing/SEARCH_MVP_v18_39.md` for historical comparison.

Actual source code is the truth. If infrastructure or permissions are unknown,
mark UNVERIFIED; don't invent live backends, database contents or provider offers.

## 2 — Core requirements

**Every search must examine the whole authorized candidate registry, irrespective
of IP, VPN, selected market or shipping destination.** A user-supplied delivery
address may boost results geographically, but MUST NOT filter other countries.
Market preference is optional and only affects priority/order. Do not ask users
to choose a region to obtain global results. Preserve all existing site blocks,
RFQ workflow, RU/EN/TR, responsive layout and design.

Registry currently contains **269 candidate references**, **266 product-related**
and 3 logistics references. Includes Russia and CIS, Türkiye, Europe, China,
Hong Kong, India, Korea, Japan, ASEAN, Middle East/Africa, North and South
America, Australia/New Zealand. New sources explicitly include Avito, Youla,
Ozon, Wildberries, Yandex Market, Trendyol, Sahibinden, letgo, n11,
eBay/Amazon regional storefronts, OLX, Mercado Libre, Facebook Marketplace,
Kleinanzeigen, Leboncoin, Gumtree, Craigslist, Carousell, Goofish,
and specialist used/auction venues Machinio, Kitmondo, EquipNet,
Surplex, Machineseeker, AllSurplus, BidSpotter, Ritchie Bros.,
IronPlanet, Grays, Superbid, MachineryTrader, Surplus Record and others.

**Don't misrepresent these as connected APIs.** They are candidate site links
for *user-initiated* discovery, not third-party crawling or synchronized feeds.
Review all source IDs, domains and realistic product relevance. Browser login,
mobile app restriction, region blocking, seller accounts and legal reuse rights
must be recorded. A 403 or JS challenge alone isn't proof a site is dead.
Mark UNCERTAIN and require actual browsing if blocked.

Required UX:
- Enter manufacturer/MPN or item text, quantity and destination. Default
  condition ANY, including new and used candidate channels.
- Show diverse high-priority supplier types in the first 12 cards.
- Show remaining candidates with incremental pagination. Do NOT cap at 13.
- Preserve manual optional category and search-engine controls. Region option
  is a ranking hint, NOT a filter.
- Support Google/Bing/Yandex/Baidu outbound searches (explicit click only),
  plus native search on allowed common eBay/Amazon/Avito/Trendyol domains.
- Support non-binding multilingual keyword variants EN/TR/DE/ZH/JA/KO/ES
  while preserving exact OEM/MPN; don't claim perfect translation.
- Private seller and auction cards must plainly say that a listing can be
  sold, withdrawn, expired or inaccessible.
- Preserve RFC/RFQ draft actions and no automatic email/vendor contact.
- No invented price, inventory, shipping quote, seller authorization,
  live auction or confirmation state.

## 3 — Handling of sold / expired listings

Review `listingLifecycle()`. Add/repair tests for:
- ended auction end date in the past;
- sold, withdrawn or removed;
- out of stock;
- stale "available" state (no recent provider evidence);
- valid current status ONLY when authorized provider gives evidence
  and a verified timestamp within a configured TTL.
- Deduplication plan by canonical listing ID, buyer premium, VAT,
  shipping origin, export compliance and machine technical condition.

eBay's authorized Browse API provides `itemEndDate` and
`estimatedAvailabilityStatus`; but no provider credentials exist here.
Do not pretend Google indexed snippets mean live inventory.
Do not connect any marketplace/private account or scrape without license.

## 4 — Run real QA, not only syntax checks

- `python3 sourcing/foundation/validate_sources.py`
- `cd sourcing/backend/functions && node --test` (Node 22)
- Browser E2E (Playwright/Chromium/WebKit if available) for source cards,
  pagination, region preferences, RU/EN/TR, native search links, RFQ
  user-triggered flows and mobile iPhone viewport.
- Test 20+ representative OEM, manufacturing, aviation, automation,
  electronics, pumps, industrial used equipment and global markets.
- Check 269 records, 266 products, 3 logistics references, no duplicate
  IDs or URLs, disabled provider APIs, no unlicensed outward network calls.
- Inspect candidate URLs for relevance and accessibility; mark clearly
  unverified/inaccessible ones and correct false/obsolete domains.
- Avoid tests contacting suppliers or initiating RFQs.

## 5 — Isolated deployment only (authorization scope)

Firebase project `geoteam-global`, tariff Spark. A second independent
Hosting site `geoteam-sourcing-20261029` is the ONLY allowed deployment
target, assuming no name collision. Do not alter the default Hosting site,
custom domain, DNS, Cloud Functions, Google Cloud Run, accounts,
databases or billing. Do not enable Blaze or install paid connectors.

Read `sourcing/deploy/publish_directory_cloud_shell.sh` first. This script
originated from v18.39/40 and must be updated to a **reviewed immutable v18.41
commit** containing every required UI, registry, test and doc. Validate
`git checkout <PIN>` and source counts 269/266. Preserve the first-pass
read-only preflight, `node --test`, Python validation, and deployment to the
specific additional Hosting target only. Do not run an unreviewed stale pin.

If Firebase CLI/Cloud Shell is authorized and safe, run preflight, make an
isolated preview, verify it, then deploy independent site and perform
HTTP readback (HTML, JS, registry, release marker). The user has permitted
this specific separate search Hosting publication, not replacing production.
If credentials unavailable, mark BLOCKED with one checked Cloud Shell command;
do not fake success or request secrets through chat.

Release integrity:
- Capture original default site release reference before changes.
- New Hosting site creation only if target ID available.
- No destructive existing-site operations.
- Validate no HTTP 404 for HTML, JS, JSON and legal/RFQ resources.
- Confirm no actual supplier stock or prices are asserted.
- Confirm no production Hosting, ticker/rfq functions changed.
- Status DEPLOYED_VERIFIED only after actual live HTTP and browser checks.
- Provide rollback instructions to disable only the independent site.

## 6 — Next phase, prepare but do NOT execute external integration

Architect source-specific adapters for approved official supplier API feeds and
search API indexes: Mouser, DigiKey, TrustedParts, Nexar/Octopart, Farnell,
Arrow, aviation channels, marketplace API agreements and direct OEM feeds.
Build normalizer for exact manufacturer+MPN+revision, OEM authorization,
license/retention restrictions, listing lifecycle, age-of-observation,
sanctions/export-control/end-use gate, stock/price evidence, landed cost,
request-state history and deduplication. Plan dedicated GeoTeam database
and bounded server workers only once the real infra is audited and approved.
No external AI/cloud/Supabase/API payments without owner permission.

## 7 — Final required report

ProductID, exact modified files, branch/commit/PR, source numbers and
breakdown by territory/channel, source URL verification coverage,
real test commands/results and browser evidence, stable verified public URL
only if deployed, actual Firebase resources touched, confirmed default site
preserved, remaining source coverage gaps, costs and quota usage, error list,
rollback and VERIFIED / NOT RUN / UNVERIFIED / BLOCKED / DEPLOYED_VERIFIED.
No unsupported "all web crawled" or "266 active supplier APIs" claims.

Goal: broad, reliable, truthful worldwide industrial supplier discovery
TODAY, preserving existing GeoTeam Global production and budget.
