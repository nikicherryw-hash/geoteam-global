# CODEX TASK — GeoTeam Global universal worldwide sourcing v18.41

**ProductID GEOTEAM_GLOBAL.** Repo: https://github.com/nikicherryw-hash/geoteam-global
Active branch: `geoteam-v18-41-universal-sourcing`.

Goal: make the globally exhaustive *source discovery* experience available on a separate Firebase Hosting site using existing approved Firebase project `geoteam-global`. Review `sourcing/UNIVERSAL_SOURCING_v18_41.md` as technical contract and inspect all current source code and history; do not replace it with a new UI or lose the RFQ drafts.

**User direction:** no supplier country selection; search all relevant sources worldwide for each part number. Include manufacturer/distributor, retailers, classifieds/private sellers, used industrial equipment, surplus dealers and auctions. Examples Avito/Ozon/Sahibinden/Trendyol/eBay/Amazon/Machinio/Surplus Record, plus China, Korea, Africa, LatAm, Oceania, Russia/CIS, EU and Americas. Optional localization affects query language and ranking only, never excludes markets. Do not blindly follow VPN/IP geolocation.

**Do in this sequence:**
1. Audit and correct 223 candidate entries; classify by source type/region and validate URL accessibility, site terms, account restrictions, search-engine indexability and privacy. Remove or mark invalid/stale entries without claiming verified integrations.
2. Run real Node 22 and Python tests, browser E2E, keyboard and iPhone/mobile responsiveness; fix any defects. Test 25 realistic MPN, machinery, aviation, used/surplus and multilingual search cases. Ensure all 220 product sources are reachable via pagination (when category relevant) rather than arbitrary caps.
3. Explicitly distinguish `SOURCE_DIRECTORY` from `LIVE_LISTING`. Listing statuses `SOLD`, `EXPIRED`, `ENDED_AUCTION`, `STALE`, `UNVERIFIED`; never show an ended eBay auction as purchasable. Code `sourcing/backend/functions/listing-status.js` is for later authorized provider data and must not be misrepresented as active frontend verification.
4. Retain Google/Bing/Yandex/Baidu external clickable search options, globally scoped exact-item searches and local language synonyms. No background scraping, credential abuse, anti-bot circumvention or unauthorized direct calls from browsers.
5. Review `sourcing/deploy/publish_directory_cloud_shell.sh` for correctly pinned source commit, checks and status; update it to v18.41 and 223/220. Never use stale v18.39/v18.40 release script.
6. Inspect Firebase `geoteam-global` Spark Hosting, deployed sites and existing `rfq`/`ticker` read-only. Do not touch the live default Hosting, DNS, billing, Node20 functions, mail service, SKS, other clouds or API keys.
7. Only if all gates pass and an authorized Firebase CLI session is available, publish a **separate** Hosting site. Check actual HTTP readback and Safari/desktop tests. If access absent, provide one exact Cloud Shell command. Do not imply deployment succeeded.
8. Design the future server-side authorized provider adapters, exact MPN identity, freshness/auction expiry, seller confirmation, deduplication, data rights, rate limits, international trade compliance and landed-cost calculation. Do not deploy unapproved API integrations or billable resources.

Provide commit links, exact VERIFIED/NOT RUN/BLOCKED status, working URL only with HTTP proof, tests, remaining gaps, cost/limits, and rollback. Do not claim automatic real-time multi-platform listings where there are only outbound search-engine links.
