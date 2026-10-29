# GeoTeam Global Search v2 — REAL OFFERS FIRST
ProductID: GEOTEAM_GLOBAL
Status: DESIGN_APPROVED_FOR_PREPARATION_ONLY; LIVE_BACKEND=NOT_CONNECTED; FIREBASE_PRODUCTION=UNCHANGED
Target: existing independent Firebase Hosting site, with an independently authorized GeoTeam search backend (not SKS, not Timeweb by assumption).
Baseline: v18.43 source-directory and published Rotax 916 reference price records.

## Business acceptance
A query is not fulfilled by listing 310 registered supplier domains. Successful results are product-specific records with original source URLs, price/currency, evidence timestamps, seller identities where published, stock/availability provenance and explicit exact/possible match state. Number of provider directories registered is NOT a measure of supplier-offer coverage.
Never treat a web search snippet as a verified stock status or binding quote.

## Search experience
- Single search bar: typed natural language, OEM P/N, manufacturer/model, exact drawing/spec, and optionally browser speech dictation RU/EN/TR.
- No required geographic or product-category selection; optional destination/condition/quantity affects ranking, never market exclusions. RFQ workflow separately requires a destination.
- Show specific offers FIRST; rank exact manufacturer+model+revision+condition before synonyms and candidates.
- Show public published prices distinct from verified live offers and supplier-confirmed quotes.
- Show up to ~10 evidence-backed offers initially, in a comparable table and detail view. Additional results paginated. Never call source-directory candidates product matches.
- After a search with zero verified offers, show "No verified price found" prominently, then supplier RFQ candidates; any manual reference price must be dated.
- For ambiguous "ротокс 916" offer "ROTAX 916 iS aircraft engine" versus ROTOX machinery; don't silently choose if multiple plausible products.
- Do not silently convert currencies or assert prices include shipping/taxes; display original currency, tax terms, condition and price date. Cross-currency comparisons need an approved dated FX source.
- Do not send RFQ/WhatsApp/emails, add to procurement registers or place orders without user action.

## Staged retrieval and fallback
A. Input normalization: preserve exact identifiers; Unicode NFKC, case/spacing, lookalikes, keyboard layouts, RU/EN/TR transliteration, probable manufacturer, family and suffix. A corrected alias is only an SUGGESTION until user or high-confidence evidence confirms.
B. Query planner: OEM/model + condition + price/currency/site variants; world-wide English and original language, plus Turkish, Russian, German, Chinese and relevant regional languages. Bounded 6-15 queries, not 310 uncontrolled requests.
C. Search broker (FUTURE, NOT DEPLOYED): self-operated GeoTeam metasearch such as SearXNG only on expressly authorized separate infrastructure with legal/terms review per engine and rate limiting, or licensed third-party official search APIs after written approval. Do not call unauthenticated public aggregators from browser as a production shortcut.
D. Candidate retrieval: URL/title/snippet is evidence only of a search lead. Deduplicate canonical URLs and prioritize OEM/authorized vendors, distributors, industrial/electronic specialty stores, used-equipment dealers, classifieds and auctions appropriate to product category.
E. Allowed data retrieval: only official feeds and permitted individual product pages with documented access/redistribution rights; respect robots, quotas, browser controls and anti-bot restrictions; no CAPTCHA bypass, no credential scraping.
F. Product matching: exact P/N+revision > OEM model > documented interchangeable alternative > weak mention. Never combine ROTOX window machinery and ROTAX aircraft engines without an explicit ambiguity signal.
G. Price extractor: price only when visible on source page or authorized API with valid ISO currency; record original raw text, original URL, observed_at, stated price date, tax and condition qualifiers. An LLM may assist extraction but cannot invent absent values.
H. Lifecycle gate: SOLD/ENDED/EXPIRED/OUT_OF_STOCK are never displayed as current offers. A live source search snippet alone cannot establish auction availability; unknown or stale remains UNVERIFIED.
I. Source confirmation: supplier-confirmed price/availability/lead time requires attributable real message/date/contact; no inferred export ability.
J. Fallback: if no actual price, show "PRICE_ON_REQUEST" with relevant verified supplier contacts (where public and permitted) and user-approved manual RFQ. Search spelling variants, obsolete identifiers, used/surplus and equivalents; do not fabricate prices, suppliers or technical compatibility.

## Price record schema (server/API contract)
Search request: POST /api/v2/search
{ "query": "Siemens 6ES7315-2EH14-0AB0", "quantity": 2, "destination": "Istanbul, Türkiye", "condition": "any", "locale": "ru" }
Search response:
{
  "status": "OFFERS_FOUND|REFERENCES_ONLY|PRICE_ON_REQUEST|NO_MATCH|TEMPORARILY_UNAVAILABLE",
  "query": "original user text",
  "canonical_product": { "manufacturer": "source-grounded", "model": "source-grounded", "part_number": "exact or null", "match_confidence": "exact|strong|possible|ambiguous" },
  "as_of": "ISO8601 UTC",
  "offers": [{
    "source_url": "exact https direct listing URL",
    "supplier": "published seller name or null",
    "part_number": "published part number or null",
    "model": "published model",
    "match_type": "EXACT|SAME_MODEL|POSSIBLE|ALTERNATIVE_REQUIRES_APPROVAL",
    "amount": null,
    "currency": null,
    "price_type": "PUBLISHED|API_OBSERVED|SELLER_CONFIRMED|PRICE_ON_REQUEST",
    "availability": "AVAILABLE_CONFIRMED|BACKORDERED|SOLD|ENDED|EXPIRED|UNKNOWN",
    "condition": "new|used|refurbished|unknown",
    "source_observed_at": "ISO8601 UTC",
    "seller_confirmed_at": null,
    "includes_shipping": null,
    "includes_tax": null,
    "export_eligibility_verified": false
  }],
  "price_references": [],
  "supplier_leads": [],
  "warnings": [],
  "coverage": { "search_queries_attempted": 0, "candidate_results": 0, "pages_verified": 0, "blocked_engines": [], "unsearched_markets": [] },
  "source_directory_matches": []
}
These are schema examples, not claimed or invented real offers. No numeric rate or quantity should be inferred from this example.

## Runtime and separation
- Firebase Spark Hosting: UI, static assets, approved citation snapshots only. It cannot execute general backend crawlers or private search credentials.
- Separate GeoTeam-owned server/API is necessary for dynamic cross-site search, throttling, database, job queue and evidence capture. Platform, owner and cost MUST be explicitly confirmed before deployment. Do not attach to SKS/Timeweb or enable Blaze by assumption.
- Preferred implementation when authorized: Python FastAPI backend + bounded async HTTP client; PostgreSQL storage owned exclusively by GeoTeam; optional self-operated SearXNG (AGPL obligations and engines' limits reviewed); Valkey/Redis if proven necessary; independent server-side speech-to-text and open model only if authorized and resourced. No paid AI/API by default.
- Browser Web Speech is optional and not universal. Some browsers transmit audio to their speech provider; explicitly disclose this and provide keyboard dictation/text fallback. No audio stored by GeoTeam front-end.
- Public backend needs TLS, rate limits, read-only abuse controls, CORS exact-origin allowlist, HTTPS URL validation, SSRF protection, egress policy, bounded redirects, timeouts, logging with PII minimization and explicit vendor data rights.

## Milestones / release gates
1. M1: UI voice dictation, destination-free discovery and honest collapsed source-directory fallback. Automated tests and browser tests required; no public deployment implied.
2. M2: owner approves actual GeoTeam search backend compute and data-search provider policy; technical preflight and backup.
3. M3: independently hosted retrieval search broker with source-specific legal adapter allowlist, data provenance capture and zero fake offers. API contract and per-provider integration tests.
4. M4: real 50-item test suite across OEM electronics, aviation, new/used equipment, pumps and obscure/discontinued P/N; grounded precision@5 and price coverage metrics. Run sample queries in RU/EN/TR. Capture blocked/captcha/stale cases as failures or warnings, not fake results.
5. M5: stage Firebase preview; manually verify desktop+mobile Safari, security, no-change checks for geoteam-global default Hosting, RFQ/ticker/functions/DNS/Spark plan; deploy only by owner permission and public HTTP readback.

## Metrics and honesty
- Offer precision@5 = verified correct product matches among top five results (don't include directory-only links).
- Price coverage = queries with >= 1 real source-cited published price / test queries, separated by category.
- Source verification = count of actually visited and permitted listing pages, NOT registry size.
- Stale auction false-positive rate must be measured; never claim 100% unavailable-item detection.
- Target thresholds are acceptance goals, not measured facts.
- Version v18.43's five Rotax references remain manually checked public examples; do not claim they generalize to arbitrary SKUs.
- Status today: M1 PREPARING, M2-M5 BLOCKED pending separate backend authorization and integration work.
