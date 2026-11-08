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
    order={"aviation":("aviation","manufacturer","marketplace","general_b2b"),
           "electronics":("electronics","manufacturer","marketplace","general_b2b"),
           "industrial":("industrial","manufacturer","marketplace","general_b2b")}[sector]
    query_words={word for word in q.replace('-', ' ').split() if len(word)>2}
    scored=sorted(_sources(),key=lambda s:(
        -sum(word in (s["name"]+" "+s["url"]).casefold() for word in query_words),
        order.index(s["segment"]) if s["segment"] in order else 4,
        int(s.get("priority",3)),s["name"].lower()))
    result=[]; seen=set()
    for s in scored:
        host=urlsplit(s["url"]).hostname or ""
        if host in seen:continue
        seen.add(host)
        result.append(s["name"]+" | "+host+" | candidate source only")
        if len(result)>=max_items:break
    return result

