"""Add the bounded public cargo estimate to the existing pilot product contract."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
anchor = "        rawOffers=report.get('offers')"
assert source.count(anchor) == 1, 'gateway contract changed; refused'
snippet = '''        cargo = raw.get('shipping_planning') if isinstance(raw.get('shipping_planning'), dict) else None
        if cargo and cargo.get('net_status') == 'SOURCE_PAGE_CHECKED':
            try:
                net = float(cargo['net_kg'])
                estimate = [float(v) for v in cargo.get('planning_gross_kg_range', [])]
                if 0 < net < 100000 and len(estimate) == 2 and net <= estimate[0] <= estimate[1] < 200000:
                    product['shipping_planning'] = {
                        'net_kg': net, 'net_status': 'SOURCE_PAGE_CHECKED',
                        'gross_kg': None, 'gross_status': 'NOT_CONFIRMED',
                        'planning_gross_kg_range': estimate,
                        'planning_status': 'ESTIMATE_NOT_CARRIER_WEIGHT'}
            except (TypeError, ValueError, KeyError):
                pass
'''
if "cargo = raw.get('shipping_planning')" not in source:
    path.write_text(source.replace(anchor, snippet + anchor, 1))
