# GeoTeam Global v18.15 — release architecture (design preview, NO PRODUCTION DEPLOY)

## Current delivered preview
- Homepage, Global Sourcing and About Us: language chooser with **EN/TR/RU active**; seven additional options deliberately disabled until professionally translated.
- Autocomplete of manufacturer names and part-number **prefixes**: internal directory hints only, not inventory listings or vendor offers.
- Optional server autocomplete contract: `GET /api/sourcing/suggest?q=Siemens%206ES7&lang=ru`.
- Test scenarios: `Siemens 6ES7`, `6ES7`, `Schneider XPSU`, `Phoenix Contact FL`, `ABB DI5`.
- Three EN/TR/RU **What We Source** pages, reciprocal hreflang pointing to staging previews; all pages explicitly `noindex,nofollow`.

## Real search architecture — NOT implemented in preview
1. Normalize query: manufacturer aliases, part-number whitespace/punctuation, OEM cross-references, genuine revision suffixes. Preserve exact original text and distinctions; don't merge similar-but-incompatible part numbers.
2. Search local verified source catalogue using PostgreSQL full-text + pg_trgm and prefix index. Deduplicate by canonical manufacturer / part / revision; rank exact > verified cross-reference > prefix/family > fuzzy. Track provenance and last-checked date.
3. Integrate **permitted** manufacturer/distributor catalogue APIs, respecting provider terms, quotas and source rights. Do not scrape protected content or invent stock/price.
4. Separate UX statuses `reference_hint`, `potential_source`, `supplier_verified`, `quote_confirmed`. Only show inventory, delivery and currency when provider data actually supports them.
5. Apply backend rate limits, 250ms debounce (frontend currently ~180ms), small caches, short request timeouts, sensitive query handling, logging with retention controls.
6. On no result: preserve entered RFQ, offer explicit WhatsApp/email/manual review. Never auto-send external messages. File upload requires approved secure backend and consent/privacy review.

### API suggestion schema (planned)
```json
{
  "suggestions": [
    {"label":"Siemens 6ES7 family","value":"Siemens 6ES7","type":"prefix"}
  ]
}
```
These values are classification suggestions **only**. Real product records require a separate verified-source contract.

## International SEO rollout — NOT LIVE
- Primary website: `https://www.geoteam-global.com/`, not the raw GitHub preview.
- Use crawlable separate same-domain routes for EN, TR, RU: `/en/`, `/tr/`, `/ru/`, and parallel paths such as `/en/what-we-source/`, `/tr/what-we-source/`, `/ru/what-we-source/`.
- Give every translated URL native language visible body copy, distinct localized title/description, language-specific internal links, self-canonical, and complete reciprocal `hreflang` including `x-default`.
- At production deploy, replace ALL staging `hreflang` URLs with production URLs. Remove staging `noindex` **only** for approved publishable pages; all previews remain `noindex`.
- Issue `sitemap.xml`; connect Google Search Console and inspect indexed pages. Preserve existing /industrial.html, /aviation.html and other known public URLs via appropriate 301 redirects after reviewing their content and traffic.
- Add Organization JSON-LD using verified corporate legal identity. Do not create fake Product/Offer schema, in-stock, reviews, certifications, distributor authorizations, prices or endorsements.
- Build in-depth pages by category, real technical terminology and justified OEM references. Avoid scaled duplicate pages, keyword stuffing and empty manufacturer/country landing pages.
- Language roadmap after EN/TR/RU: DE, FR, ES, IT, PT, AR, ZH. Publish only after translations and localization of SEO titles, notices and category content; comply with trade requirements for each RFQ and destination.
- Russian is a language option, not a claim that all products can be supplied to Russia. All proposed supply routes require relevant sanctions/export-control and end-use screening.

## Publish gate
- User approves EN/TR/RU copy and final visual.
- Product search adapter tested against authorized sources with real test fixtures; no inferred pricing.
- RFQ receiving system and privacy/security notices approved.
- Manual desktop/mobile regression (typed suggestions, keyboard operation, language selection, RFQ fallback).
- Separate staging and production hosting; do not deploy to live Firebase hosting without an explicit release step.
