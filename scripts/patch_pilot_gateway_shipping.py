"""Add the bounded public cargo estimate to the existing pilot product contract."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
anchor = "    rawoffers=report.get('offers')"
assert source.count(anchor) == 1, 'gateway contract changed; refused'
snippet = "    product['shipping_planning']=raw.get('shipping_planning')\n"
if "product['shipping_planning']" not in source:
    path.write_text(source.replace(anchor, snippet + anchor, 1))
