# GeoTeam Global — рабочий поисковый пилот v18.39

**ProductID**: GEOTEAM_GLOBAL. **Status**: PREPARED, branch-only. **Date**: 2026-10-29.
Production, DNS, old RFQ functions, mail API, company databases and SKS: **UNCHANGED**.

## What actually works right now

- `preview-v18-7/sourcing.html`: existing RU / EN / TR website, RFQ draft, manufacturer hints and product search UI.
- `preview-v18-7/global-source-finder.js`: product-category routing and real outbound source-discovery searches.
- `preview-v18-7/data/sources.v1.json`: 44 global sources; 41 supplier/catalog candidates and 3 logistics candidates.
- `sourcing/backend/functions/`: Node.js 22 Firebase HTTP function source, with exactly three GET endpoints:
  `/api/sourcing/health`, `/api/sourcing/suggest`, `/api/sourcing/search`.

**Search mode: SOURCE_DISCOVERY_ONLY.** Search recommends public, real supplier websites.
Clicking `Search this part` opens a public web search restricted to the supplier domain.
Clicking `Open source` opens the original supplier website. Neither action guarantees
the supplier has that part in stock. **No supplier API is connected, and no API key
is included, no stock or price is fabricated or automatically checked.**
No background third-party browsing or supplier mail is initiated by the pilot.

## Manual acceptance, including iPhone

1. Open `preview-v18-7/sourcing.html?lang=ru` from the v18.39 GitHub raw.githack preview.
2. Enter `Siemens 6ES7315-2EH14-0AB0`, quantity 2, destination `Istanbul, Türkiye`.
3. Press `Проверить источники`; an actual source shortlist should replace the old preview disclaimer.
4. Confirm cards are meaningful: distributors of electronic components plus industrial suppliers.
5. Open `Искать артикул` on a selected card: an external site-filtered search opens only after the click.
6. Select `Авиационные компоненты` and search `2042M67P02`; see aviation sources.
7. Test `насос Иртыш ПФ2`, `клапан Ду150`, `Boeing 737 actuator` and a drawing/RFQ request.
8. Check RU/TR/EN and responsive layout. Check that `Добавить позицию`,
   `Копировать RFQ`, `RFQ по email` and WhatsApp still require user action.
9. Confirm no price, available quantity or lead time is shown without supplier evidence.

**UI/browser execution on iPhone is NOT VERIFIED** until tested in an actual Safari session.

## Reproducible Node.js verification (Node 22)

```bash
cd sourcing/backend/functions
node --test
```

Tests cover 11 product categories/languages, 44/41 source registry,
source provenance flags, /health, /search, /suggest, input validation,
URL scheme blocking, GET-only API and 35/min local rate throttle.
This repository's Firebase function uses `firebase-functions/v2/https`
but the test suite does not require a real mail API, cloud credentials, or external sends.

## Exact files to deploy LATER, after preflight

Frontend in the verified **GeoTeam** hosting project:
- `sourcing.html`
- `global-source-finder.js`
- `data/sources.v1.json`
- original site files and legal notices

Backend in verified **GeoTeam** functions source directory:
- `index.js` (function export: `sourcing`)
- `directory-api.js`
- `source-finder.js`
- `source_registry.json`
- `package.json`
- install with `npm ci` only when an approved lockfile exists; otherwise `npm install`
  in isolated staging to generate an audited lockfile before production.

**Important:** `sourcing/backend/hosting-rewrite.example.json` is illustrative only.
The live Firebase `firebase.json` already has an older `/rfq` rewrite.
Do **not** replace `firebase.json`; merge a specific
`/api/sourcing/**` rewrite preserving all existing rewrites/rules.
Do not replace the old `functions/index.js` and accidentally remove RFQ:
merge the `sourcing` export into the verified current functions source,
or use a separate Firebase codebase after auditing the deployed configuration.
Current Firebase ownership, billing, project ID, existing function revisions
and Firebase CLI authenticated access are **UNVERIFIED**.

### Staging workflow (requires authenticated GeoTeam project and approval)

1. Identify actual Firebase project ID and Hosting site serving the live domain.
2. Record existing current Hosting release, Functions revisions, secrets *names*,
   current `firebase.json`, authorized domains, billing limits.
3. Backup the existing release/config and establish rollback.
4. Run `node --test` and Firebase Emulator Suite in a dedicated staging checkout.
5. Use a **Firebase Hosting preview channel**, not a production deploy.
6. Test browser source discovery and server endpoints from the same preview domain.
7. Approve deployment and explicitly promote only a reviewed release.
8. After production install: verify GET /api/sourcing/health, three search
   categories, RFQ draft and old RFQ function; revert Hosting to the recorded
   previous release and disable the new rewrite/function if acceptance fails.

Do not run `firebase deploy` from arbitrary legacy source or guess the
project ID. No SKS or Timeweb resources may be reused by assumption.

## Extension path to true aggregating global search

1. Obtain approved API licenses/credentials for Mouser, DigiKey, Nexar,
   TrustedParts, aviation platforms and relevant direct distributors.
2. Add source-specific adapters under quotas with per-source timeouts and
   allowlisted egress; never scrape logged-in/regulated listings without rights.
3. Add separate GeoTeam PostgreSQL for normalized MPN/manufacturer/revision,
   licensed listings and observation time; move beyond the immutable source JSON.
4. Add request state machine and customer auth only after privacy and security QA.
5. Build landed-cost estimates from **verified** origin, destination,
   HS code, incoterms, carrier rates and applicable duties/taxes.
6. Add explicit export/end-user/end-use compliance gates before RFQs,
   payment, shipping or binding supplier communications.

## Status, risks, rollback

- Source and mock HTTP API logic: VERIFIED in isolated code-mode QA.
- `node --test` in actual Node22 runtime: NOT RUN in this connector environment.
- Browser on GitHub preview: UNVERIFIED.
- Firebase deployment, live provider API, stock and prices: BLOCKED (credentials and access).
- Rollback of PREPARED changes: discard preview branch. No production effect.
