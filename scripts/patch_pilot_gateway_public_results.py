"""Create, but never install, a public-result-safe pilot gateway candidate.

Run on the staging host against the inspected pilot_gateway.py.  It fails closed if
the expected source layout is not present and writes a sibling .new file only.
"""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"REFUSED_{label}: expected one exact source marker")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_pilot_gateway_public_results.py /path/to/pilot_gateway.py")
    source = Path(sys.argv[1])
    # Server-side files can have been edited from Windows; normalize before
    # guarded source matching and always write the candidate with LF.
    text = source.read_text(encoding="utf-8").replace("\r\n", "\n")
    text = replace_once(
        text,
        "from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response\n",
        "from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Request, Response\n"
        "from fastapi.responses import StreamingResponse\n",
        "import",
    )
    text = replace_once(
        text,
        "from .ai_search import search_once\n",
        "from .ai_search import fetch_public_image, search_once\n",
        "ai-import",
    )
    text = replace_once(
        text,
        "        db.execute('CREATE INDEX IF NOT EXISTS idx_pilot_created ON jobs(created_at)')\n",
        "        db.execute('CREATE INDEX IF NOT EXISTS idx_pilot_created ON jobs(created_at)')\n"
        "        db.execute('CREATE TABLE IF NOT EXISTS job_internal_sources ('\n"
        "                   'job_id TEXT PRIMARY KEY, sources TEXT NOT NULL, '\n"
        "                   'representative_image_url TEXT, created_at INTEGER NOT NULL, '\n"
        "                   'FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE)')\n",
        "db-schema",
    )
    text = replace_once(
        text,
        "        db.execute('UPDATE jobs SET status=?,updated_at=?,report=?,error=? WHERE id=?',\n"
        "                   (status, int(time.time()), payload, error, job_id))\n\n\n"
        "async def _work",
        "        db.execute('UPDATE jobs SET status=?,updated_at=?,report=?,error=? WHERE id=?',\n"
        "                   (status, int(time.time()), payload, error, job_id))\n\n\n"
        "def _store_internal_sources(job_id, sources, representative_image_url):\n"
        "    \"\"\"Persist source evidence server-side only; never include it in client JSON.\"\"\"\n"
        "    clean_sources = sources if isinstance(sources, list) else []\n"
        "    payload = json.dumps(clean_sources, ensure_ascii=False, allow_nan=False)\n"
        "    with _connect() as db:\n"
        "        db.execute('INSERT OR REPLACE INTO job_internal_sources '\n"
        "                   '(job_id,sources,representative_image_url,created_at) VALUES (?,?,?,?)',\n"
        "                   (job_id, payload, representative_image_url or None, int(time.time())))\n\n\n"
        "async def _work",
        "store-helper",
    )
    text = replace_once(
        text,
        "        if result.get('product_id') != 'GEOTEAM_GLOBAL':\n"
        "            raise ValueError('INVALID_PRODUCT')\n"
        "        result['pilot'] = budget.status()\n",
        "        if result.get('product_id') != 'GEOTEAM_GLOBAL':\n"
        "            raise ValueError('INVALID_PRODUCT')\n"
        "        internal_sources = result.pop('_internal_sources', [])\n"
        "        representative_image_url = result.pop('_representative_image_url', None)\n"
        "        _store_internal_sources(job_id, internal_sources, representative_image_url)\n"
        "        if representative_image_url:\n"
        "            image_path = '/api/v1/guest/research/' + job_id + '/image'\n"
        "            result['image'] = image_path\n"
        "            if isinstance(result.get('product'), dict):\n"
        "                result['product']['image'] = image_path\n"
        "        result['pilot'] = budget.status()\n",
        "worker-contract",
    )
    text = replace_once(
        text,
        "def _gt_peer(request):\n"
        "    # Never trust X-Forwarded-For supplied by arbitrary clients.\n"
        "    addr = request.client.host if request.client else 'unknown'\n"
        "    return _gt_hmac.new(_GT_PEER_SALT.encode(), addr.encode(), _gt_hashlib.sha256).hexdigest()\n\n",
        "def _gt_peer(request):\n"
        "    # Never trust X-Forwarded-For supplied by arbitrary clients.\n"
        "    addr = request.client.host if request.client else 'unknown'\n"
        "    return _gt_hmac.new(_GT_PEER_SALT.encode(), addr.encode(), _gt_hashlib.sha256).hexdigest()\n\n\n"
        "@app.get('/api/v1/guest/research/{job_id}/image')\n"
        "async def geoteam_guest_research_image(request: Request, job_id: str):\n"
        "    \"\"\"Same-origin image proxy: a seller URL is never sent to a browser.\"\"\"\n"
        "    _gt_guard(request)\n"
        "    if not _gt_re.fullmatch('[a-f0-9]{32}', job_id):\n"
        "        raise HTTPException(404, 'NOT_FOUND')\n"
        "    with _connect() as db:\n"
        "        row = db.execute('SELECT representative_image_url FROM job_internal_sources WHERE job_id=?',\n"
        "                         (job_id,)).fetchone()\n"
        "    image_url = row['representative_image_url'] if row else None\n"
        "    if not image_url:\n"
        "        raise HTTPException(404, 'IMAGE_NOT_AVAILABLE')\n"
        "    image = await fetch_public_image(str(image_url))\n"
        "    if not image:\n"
        "        raise HTTPException(404, 'IMAGE_NOT_AVAILABLE')\n"
        "    return StreamingResponse(iter([image[0]]), media_type=image[1], headers={\n"
        "        'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})\n\n",
        "guest-image-route",
    )
    candidate = source.with_name(source.name + ".public-results.new")
    candidate.write_text(text, encoding="utf-8")
    print(f"CANDIDATE_WRITTEN={candidate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
