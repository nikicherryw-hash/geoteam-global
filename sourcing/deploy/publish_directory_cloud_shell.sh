#!/usr/bin/env bash
# GeoTeam Global, v18.42: publish SECOND Firebase Hosting site, leave main site/Functions untouched.
set -Eeuo pipefail
PROJECT="geoteam-global"
SITE="${GEOTEAM_SITE_ID:-geoteam-sourcing-20261029}"
PIN="${GEOTEAM_SOURCE_SHA:-}"
BRANCH="geoteam-v18-42-search-engine"
REPO="https://github.com/nikicherryw-hash/geoteam-global.git"

echo "=== GEOTEAM SEARCH RELEASE / PREFLIGHT ==="
[[ "$PIN" =~ ^[0-9a-f]{40}$ ]] || { echo "BLOCKED: set explicit GEOTEAM_SOURCE_SHA (reviewed 40-char commit)." >&2; exit 9; }
[[ "$SITE" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]] && [[ "$SITE" != "$PROJECT" ]] || { echo "BLOCKED: unsafe Hosting site ID" >&2; exit 9; }
echo "PROJECT=$PROJECT SEPARATE_SITE=$SITE PIN=$PIN"
for c in firebase git python3 node curl; do
  command -v "$c" >/dev/null || { echo "BLOCKED: missing $c" >&2; exit 10; }
done
firebase hosting:sites:get geoteam-global --project "$PROJECT" >/dev/null ||
  { echo "BLOCKED: main GeoTeam Hosting not accessible" >&2; exit 11; }
echo "EXISTING_SITES:"
firebase hosting:sites:list --project "$PROJECT"
if firebase hosting:sites:get "$SITE" --project "$PROJECT" >/dev/null 2>&1; then
  echo "BLOCKED: destination site already exists; no overwrite." >&2
  exit 12
fi

WORK="$(mktemp -d)"
SRC="$WORK/repo"
OUT="$WORK/publish"
mkdir -p "$OUT/public/data" "$OUT/public/en" "$OUT/public/ru" "$OUT/public/tr"
git clone --quiet --depth 150 --single-branch --branch "$BRANCH" "$REPO" "$SRC"
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] || { echo "BLOCKED: approved SHA differs from branch HEAD." >&2; exit 13; }
git -C "$SRC" checkout --quiet --detach "$PIN" ||
  { echo "BLOCKED: pinned source commit unavailable; no deployment." >&2; exit 13; }
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$PIN" ]] ||
  { echo "BLOCKED: source commit changed; no deployment." >&2; exit 13; }

FILES=(
 sourcing.html global-source-finder.js data/sources.v1.json
 about.html privacy.html rfq-privacy.html
 en/what-we-source.html ru/what-we-source.html tr/what-we-source.html
)
for f in "${FILES[@]}"; do
  [[ -s "$SRC/preview-v18-7/$f" ]] ||
    { echo "BLOCKED: missing file: $f" >&2; exit 14; }
  cp "$SRC/preview-v18-7/$f" "$OUT/public/$f"
done

python3 - "$OUT/public" "$PIN" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]); sha=sys.argv[2]
r=json.loads((p/"data/sources.v1.json").read_text())
assert r["product_id"]=="GEOTEAM_GLOBAL" and len(r["sources"])==313
assert sum(s["segment"]!="logistics" for s in r["sources"])==310
assert all(s["enabled"] is False and s["integration_status"]=="NOT_CONNECTED" and s["rights_status"]=="NOT_REVIEWED" for s in r["sources"])
assert all(s["source_type"] and s["listing_status_capability"]=="UNVERIFIED_NO_API" for s in r["sources"] if s["segment"]!="logistics")
f=p/"sourcing.html"
html=f.read_text()
assert 'global-source-finder.js' in html and 'id="gtSector"' in html
assert "engine.search({...req,sector,region:\'all\',condition:req.condition})" in html
assert 'id="gtMarketRegion"' not in html and 'id="gtSearchEngine"' not in html
assert 'gt-global-auto-banner' in html
f.write_text(html.replace('href="index.html"','href="https://geoteam-global.com/"'))
(p/"index.html").write_text("""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="refresh" content="0;url=/sourcing.html?lang=ru">
<title>GeoTeam Global — Глобальный поиск</title></head>
<body><a href="/sourcing.html?lang=ru">Глобальный поиск поставщиков</a></body></html>""")
(p/"contact.html").write_text("""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="refresh" content="0;url=https://geoteam-global.com/contact.html">
<title>Контакты GeoTeam Global</title></head>
<body><a href="https://geoteam-global.com/contact.html">Контакты</a></body></html>""")
(p/"robots.txt").write_text("User-agent: *\nDisallow: /\n")
(p/"release.json").write_text(json.dumps({"product_id":"GEOTEAM_GLOBAL",
    "version":"v18.42","git_sha":sha,"search_mode":"SOURCE_DISCOVERY_ONLY",
    "supplier_api_connected":False,"prices_verified":False},indent=2)+"\n")
print("SOURCE_PREFLIGHT=PASS SOURCES=313 PRODUCT_SOURCES=310")
PY

cat > "$OUT/firebase.json" <<'JSON'
{
  "hosting":{
    "target":"sourcing","public":"public",
    "ignore":["firebase.json","**/.*","**/node_modules/**"],
    "headers":[
      {"source":"**/*.html","headers":[
        {"key":"X-Content-Type-Options","value":"nosniff"},
        {"key":"Referrer-Policy","value":"strict-origin-when-cross-origin"}]},
      {"source":"**/*.json","headers":[
        {"key":"Cache-Control","value":"public,max-age=300"}]}
    ]
  }
}
JSON
printf '{"projects":{"default":"%s"}}\n' "$PROJECT" > "$OUT/.firebaserc"

echo "=== RUN AUTOMATED TESTS BEFORE ANY CLOUD WRITE ==="
NODE_MAJOR="$(node -p 'Number(process.versions.node.split(".")[0])')"
if (( NODE_MAJOR < 22 )); then
  echo "BLOCKED: Node.js 22+ required for GeoTeam tests and future Functions compatibility." >&2
  exit 15
fi
python3 "$SRC/sourcing/foundation/validate_sources.py"
(cd "$SRC/sourcing/backend/functions" && node --test)
echo "NODE_TESTS=PASS"

echo "=== ADDITIONAL PREFLIGHT BEFORE CLOUD WRITE ==="
node --check "$SRC/preview-v18-7/global-source-finder.js"
node --check "$SRC/sourcing/backend/functions/source-finder.js"
node --check "$SRC/sourcing/backend/functions/directory-api.js"
bash -n "$SRC/sourcing/deploy/publish_directory_cloud_shell.sh"
MAIN_BASE="https://${PROJECT}.web.app"
curl -fLsS --max-time 25 "$MAIN_BASE/" -o "$WORK/main-before.html" || { echo "BLOCKED: default Hosting HTTP unavailable." >&2; exit 16; }
echo "=== CREATE ISOLATED HOSTING SITE (MAIN SITE UNCHANGED) ==="
firebase hosting:sites:create "$SITE" --project "$PROJECT"
cd "$OUT"
firebase target:apply hosting sourcing "$SITE" --project "$PROJECT"
echo "=== PREVIEW CHANNEL ==="
firebase hosting:channel:deploy sourcing-preflight \
  --only sourcing --expires 1d --project "$PROJECT" --non-interactive
echo "=== PUBLISH ONLY NEW HOSTING SITE ==="
firebase deploy --only hosting:sourcing --project "$PROJECT" \
  --non-interactive --message "GeoTeam Global directory search v18.42 ($PIN)"

echo "=== LIVE READBACK ==="
BASE="https://${SITE}.web.app"
curl -fLsS --retry 5 --retry-all-errors --retry-delay 2 --max-time 25 \
  "$BASE/sourcing.html" -o "$WORK/live.html"
curl -fLsS --retry 5 --retry-all-errors --retry-delay 2 --max-time 25 \
  "$BASE/global-source-finder.js" -o "$WORK/live.js"
curl -fLsS --retry 5 --retry-all-errors --retry-delay 2 --max-time 25 \
  "$BASE/data/sources.v1.json" -o "$WORK/live.json"
curl -fLsS --retry 5 --retry-all-errors --retry-delay 2 --max-time 25 \
  "$BASE/release.json" -o "$WORK/release.json"
python3 - "$WORK" "$PIN" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]); pin=sys.argv[2]
assert 'id="gtSector"' in (p/"live.html").read_text()
assert 'id="gtMarketRegion"' not in (p/"live.html").read_text()
assert 'id="gtSearchEngine"' not in (p/"live.html").read_text()
assert "gt-global-auto-banner" in (p/"live.html").read_text()
assert "GeoTeamSourceFinder" in (p/"live.js").read_text()
assert "listingLifecycle" in (p/"live.js").read_text()
assert "multilingualVariants" in (p/"live.js").read_text()
assert len(json.loads((p/"live.json").read_text())["sources"])==313
assert json.loads((p/"release.json").read_text())["git_sha"]==pin
print("LIVE_READBACK=PASS")
PY
echo "PUBLIC_SEARCH_URL=$BASE/sourcing.html?lang=ru"
echo "ORIGINAL_SITE=https://geoteam-global.com/ (UNCHANGED)"
echo "DIRECTORY_MODE=YES PRODUCT_SOURCE_CANDIDATES=310 LIVE_PROVIDER_API_CONNECTED=0"
echo "LOCAL_AUDIT_FILES=$WORK"
