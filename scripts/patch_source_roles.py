"""Generate gateway candidate; preserve strict customer serialization."""
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
marker = "        offers.append({k:v for k,v in q.items() if v and k != 'item'})"
if text.count(marker) != 1:
    raise SystemExit('REFUSED_SOURCE_ROLE_MARKER')
replacement = """        role = o.get('source_role', 'PRODUCT_OFFER')
        if role not in {'PRODUCT_OFFER','MANUFACTURER','OFFICIAL_REPRESENTATIVE','POTENTIAL_SUPPLIER'}:
            role = 'POTENTIAL_SUPPLIER'
        q['source_role'] = role
        for field in ('seller_country','dispatch_country','manufacturing_country','price_unit'):
            q[field] = txt(o.get(field), 80)
        if role != 'PRODUCT_OFFER':
            q['price'] = q['currency'] = ''
            q['availability'] = 'NOT_CONFIRMED'
            q['status'] = 'PROCUREMENT_CHANNEL'
        offers.append({k:v for k,v in q.items() if v and k != 'item'})"""
text = text.replace(marker, replacement, 1)
path.with_name(path.name + '.source-roles.new').write_text(text, encoding='utf-8')
print('CANDIDATE_READY')
