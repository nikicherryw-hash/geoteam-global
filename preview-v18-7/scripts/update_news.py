#!/usr/bin/env python3
"""Refresh GeoTeam preview headlines from public RSS; do not fabricate missing news."""
from __future__ import annotations
import datetime as dt
import email.utils
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

NOW = dt.datetime.now(dt.timezone.utc)
ROOT = Path(__file__).resolve().parents[1] / "data"

def search_feed(q, lang, country):
    params = urllib.parse.urlencode({
        "q": q + " when:7d",
        "hl": lang,
        "gl": country,
        "ceid": country + ":" + lang.split("-")[0]
    })
    return "https://news.google.com/rss/search?" + params

FEEDS = {
    "ru": [
        ("ФНС России", "RU", "https://www.nalog.gov.ru/rn77/rss/"),
        ("Google Новости", "RU", search_feed("промышленное оборудование OR международная логистика OR таможенные правила", "ru", "RU"))
    ],
    "en": [
        ("EASA", "EU", "https://www.easa.europa.eu/newsroom-and-events/news/feed.xml"),
        ("European Commission", "EU", "https://ec.europa.eu/taxation_customs/node/2/rss_en"),
        ("WTO", "UN", "https://www.wto.org/library/rss/latest_news_e.xml")
    ],
    "tr": [
        ("Google Haberler", "TR", search_feed("gümrük OR sanayi tedarik zinciri OR lojistik", "tr", "TR"))
    ]
}

def get_text(item, tag):
    element = item.find(tag)
    return "".join(element.itertext()).strip() if element is not None else ""

def date_of(value):
    if not value:
        return None
    try:
        d = email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None: d = d.replace(tzinfo=dt.timezone.utc)
        return d.date()
    except (ValueError, TypeError, IndexError):
        try:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            return None

def collect(url, source, country):
    request = urllib.request.Request(url, headers={
        "User-Agent": "GeoTeamGlobal-PreviewNewsRSS/1.0",
        "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml"
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError("Unexpected RSS status")
        content = response.read(2_000_001)
    if len(content) > 2_000_000:
        raise RuntimeError("RSS too large")
    doc = ET.fromstring(content)
    entries = doc.findall(".//item") or doc.findall("{http://www.w3.org/2005/Atom}entry")
    result = []
    for item in entries[:35]:
        title = get_text(item, "title") or get_text(item, "{http://www.w3.org/2005/Atom}title")
        title = html.unescape(re.sub(r"<[^>]*>", "", title)).strip()
        url = get_text(item, "link")
        if not url:
            link = item.find("{http://www.w3.org/2005/Atom}link")
            url = link.attrib.get("href", "") if link is not None else ""
        published = date_of(get_text(item, "pubDate") or
                            get_text(item, "{http://www.w3.org/2005/Atom}updated") or
                            get_text(item, "{http://www.w3.org/2005/Atom}published") or
                            get_text(item, "{http://purl.org/dc/elements/1.1/}date"))
        if not published or not title or len(title) < 12:
            continue
        days = (NOW.date() - published).days
        parsed = urllib.parse.urlparse(url)
        if not (-1 <= days <= 14) or parsed.scheme != "https" or not parsed.hostname:
            continue
        result.append({"title": title[:240], "source": source, "country": country,
                       "date": published.isoformat(), "url": url})
    return result

if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    refreshed = 0
    for lang, feeds in FEEDS.items():
        items, errors, visited = [], [], set()
        for source, country, feed in feeds:
            try:
                for item in collect(feed, source, country):
                    url = item["url"]
                    if url in visited: continue
                    visited.add(url)
                    items.append(item)
            except (OSError, RuntimeError, ET.ParseError, ValueError) as exc:
                errors.append(source + ": " + type(exc).__name__)
        items.sort(key=lambda item: item["date"], reverse=True)
        if not items:
            print(lang + " NO_NEW_ITEMS: keeping previous file; errors=" + str(errors))
            continue
        output = {"generated_at": NOW.isoformat().replace("+00:00", "Z"),
                  "mode": "automatic_rss", "items": items[:12]}
        target = ROOT / ("ticker-live-" + lang + ".json")
        target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        refreshed += 1
        print(lang + " UPDATED=" + str(len(output["items"])) + " errors=" + str(errors))
    if refreshed == 0:
        raise SystemExit("BLOCKED: all RSS sources unavailable; no files overwritten")
