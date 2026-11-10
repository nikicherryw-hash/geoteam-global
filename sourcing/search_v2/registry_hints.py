"""Pick a SMALL, relevant set of GeoTeam registry hints, never represent as found listings."""
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit
from .core import identity, normalized

REGISTRY=Path(__file__).resolve().parents[1]/"backend"/"functions"/"source_registry.json"

@lru_cache(maxsize=1)
def _sources():
    data=json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data["product_id"]=="GEOTEAM_GLOBAL"
    return tuple(x for x in data["sources"] if x.get("segment")!="logistics")

def pick(query: str, max_items: int=12) -> list[str]:
    if not 0 <= max_items <= 12: raise ValueError("max_items must be <= 12")
    q=normalized(query).casefold()
    sector="aviation" if identity(query).get("manufacturer")=="ROTAX" else (
        "aviation" if any(w in q for w in ("boeing","airbus","aircraft","вертолет","авиаци")) else
        "industrial" if any(w in q for w in ("ship", "marine", "vessel", "судов", "морск", "gemi")) else
        "electronics" if any(w in q for w in ("siemens","abb","phoenix","eaton","omron","schneider","plc","автоматик")) else
        "industrial"
    )
    if max_items == 0:
        return []
    query_words={word for word in q.replace('-', ' ').split() if len(word)>2}
    scored=sorted(_sources(),key=lambda s:(
        -sum(word in (s["name"]+" "+s["url"]).casefold() for word in query_words),
        int(s.get("priority",3)),s["name"].lower()))
    result=[]; seen=set()
    def add(s):
        host=urlsplit(s["url"]).hostname or ""
        if host in seen:
            return False
        seen.add(host)
        result.append(s["name"]+" | "+host+" | candidate source only")
        return True
    # Discovery hints must not be consumed entirely by one sector. Give the
    # model a relevant technical starting point and several world regions.
    for segment, count in ((sector, 4), ("manufacturer", 1)):
        for s in (row for row in scored if row["segment"] == segment):
            if len(result) >= min(max_items, count if segment == sector else 5):
                break
            if segment == "manufacturer" and not any(
                    word in (s["name"] + " " + s["url"]).casefold() for word in query_words):
                continue
            add(s)
    markets = [s for s in scored if s["segment"] == "marketplace"]
    regions = ("north_america", "europe", "china", "asia", "latin_america", "oceania", "turkey", "russia")
    market_target = min(max_items, 11)
    for region in regions:
        if len(result) >= market_target:
            break
        for s in markets:
            if region in s.get("scope", []) and add(s):
                break
    for segment in ("general_b2b", sector, "marketplace", "industrial", "electronics", "aviation"):
        for s in (row for row in scored if row["segment"] == segment):
            if len(result) >= max_items:
                return result
            add(s)
    return result
