#!/usr/bin/env bash
set -euo pipefail
base=/srv/geoteam-staging/current
code=/opt/geoteam-global-ai
stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup=/srv/geoteam-staging/backups/searchfix-$stamp
mkdir -p "$backup/staged/preview-v18-7" "$backup/staged/sourcing/search_v2"
cp -a "$base/index.html" "$backup/index.html.before"
cp -a "$code/sourcing/search_v2/batch_document.py" "$backup/batch_document.py.before"
cp -a "$base/index.html" "$backup/staged/preview-v18-7/index.html"
cp -a "$code/sourcing/search_v2/batch_document.py" "$backup/staged/sourcing/search_v2/batch_document.py"
sha256sum "$backup/index.html.before" "$backup/batch_document.py.before" > "$backup/SHA256SUMS.before"
curl -fsSL https://raw.githubusercontent.com/nikicherryw-hash/geoteam-global/codex/account-quote-drafts-20261110/staging-payload-20261110-searchfix/searchfix.patch -o "$backup/searchfix.patch"
patch --batch --fuzz=0 -p1 -d "$backup/staged" --dry-run < "$backup/searchfix.patch"
patch --batch --fuzz=0 -p1 -d "$backup/staged" < "$backup/searchfix.patch"
"$code/.venv/bin/python" -m py_compile "$backup/staged/sourcing/search_v2/batch_document.py"
if ! grep -q 'href="account.html?lang=en"' "$backup/staged/preview-v18-7/index.html"; then echo SIGNIN_PREFLIGHT_FAILED; exit 1; fi
cp -a "$backup/staged/preview-v18-7/index.html" "$base/index.html.new"
cp -a "$backup/staged/sourcing/search_v2/batch_document.py" "$code/sourcing/search_v2/batch_document.py.new"
mv "$base/index.html.new" "$base/index.html"
mv "$code/sourcing/search_v2/batch_document.py.new" "$code/sourcing/search_v2/batch_document.py"
PYTHONPATH="$code" "$code/.venv/bin/python" -m unittest sourcing.search_v2.test_batch_document
systemctl restart geoteam-ai-pilot
echo "BACKUP=$backup"
echo "ROLLBACK=cp -a $backup/index.html.before $base/index.html; cp -a $backup/batch_document.py.before $code/sourcing/search_v2/batch_document.py; systemctl restart geoteam-ai-pilot"
