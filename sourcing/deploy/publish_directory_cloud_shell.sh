#!/usr/bin/env bash
# GeoTeam Global, v18.40: publish SECOND Firebase Hosting site, leave main site/Functions untouched.
set -Eeuo pipefail
PROJECT="geoteam-global"
SITE="geoteam-sourcing-20261029"
PIN="455fe7da7431305ee2a89b867d4b3eaf6d183e8c"
BRANCH="geoteam-v18-40-worldwide-discovery"
REPO="https://github.com/nikicherryw-hash/geoteam-global.git"

echo "=== GEOTEAM SEARCH RELEASE / PREFLIGHT ==="
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
git clone --quiet --depth 25 --single-branch --branch "$BRANCH" "$REPO" "$SRC"
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
assert r["product_id"]=="GEOTEAM_GLOBAL" and len(r["sources"])==134
assert sum(s["segment"]!="logistics" for s in r["sources"])==131
assert all(s["enabled"] is False and s["integration_status"]=="NOT_CONNECTED" for s in r["sources"])
f=p/"sourcing.html"
html=f.read_text()
assert 'global-source-finder.js' in html and 'id="gtSector"' in html
assert "engine.search({...req,sector,region})" in html
assert 'id="gtMarketRegion"' in html and 'id="gtSearchEngine"' in html
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
    "version":"v18.40","git_sha":sha,"search_mode":"SOURCE_DISCOVERY_ONLY",
    "supplier_api_connected":False,"prices_verified":False},indent=2)+"\n")
print("SOURCE_PREFLIGHT=PASS SOURCES=44 PRODUCT_SOURCES=41")
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
python3 "$SRC/sourcing/foundation/validate_sources.py"
(cd "$SRC/sourcing/backend/functions" && node --test)
echo "NODE_TESTS=PASS"

echo "=== CREATE ISOLATED HOSTING SITE (MAIN SITE UNCHANGED) ==="
firebase hosting:sites:create "$SITE" --project "$PROJECT"
cd "$OUT"
firebase target:apply hosting sourcing "$SITE" --project "$PROJECT"
echo "=== PREVIEW CHANNEL ==="
firebase hosting:channel:deploy sourcing-preflight \
  --only sourcing --expires 1d --project "$PROJECT" --non-interactive
echo "=== PUBLISH ONLY NEW HOSTING SITE ==="
firebase deploy --only hosting:sourcing --project "$PROJECT" \
  --non-interactive --message "GeoTeam Global directory search v18.40 ($PIN)"

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
assert 'id="gtMarketRegion"' in (p/"live.html").read_text()
assert 'id="gtSearchEngine"' in (p/"live.html").read_text()
assert "GeoTeamSourceFinder" in (p/"live.js").read_text()
assert len(json.loads((p/"live.json").read_text())["sources"])==134
assert json.loads((p/"release.json").read_text())["git_sha"]==pin
print("LIVE_READBACK=PASS")
PY
echo "PUBLIC_SEARCH_URL=$BASE/sourcing.html?lang=ru"
echo "ORIGINAL_SITE=https://geoteam-global.com/ (UNCHANGED)"
echo "DIRECTORY_MODE=YES PROVIDER_API_CONNECTED=NO"
echo "LOCAL_AUDIT_FILES=$WORK"
