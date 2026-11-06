"""Extract offer facts only from a matching Product's structured source data."""
import json
import re
from html.parser import HTMLParser


class StructuredData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.current = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = dict(attrs).get('type', '').lower() == 'application/ld+json'
            self.current = []

    def handle_data(self, data):
        if self.active:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.blocks.append(''.join(self.current))
            self.active = False


class ProductTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None
        self.visible, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script','style'}:
            self.hidden += 1
        if tag == 'tr':
            self.row = []
        if tag in {'td','th'} and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)
            if self.cell is not None:
                self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {'script','style'}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {'td','th'} and self.cell is not None:
            self.row.append(' '.join(' '.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def table_facts(page, model):
    parser = ProductTable()
    parser.feed(page[:500000])
    # Match complete P/N tokens, retaining suffixes: -3AAR is not -3.
    codes = re.findall(r'[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)+', str(model))
    if not codes:
        return {}
    target = max(codes, key=len).upper()
    headers, matches = [], []
    for row in parser.rows:
        lower = [x.lower().strip() for x in row]
        if any(x in {'part number','part no','p/n','pn','part #'} for x in lower):
            headers = lower
            continue
        if not any(target in [x.upper() for x in re.findall(r'[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)+', cell)] for cell in row):
            continue
        facts = {}
        for index, heading in enumerate(headers):
            if index >= len(row):
                continue
            value = row[index].strip()
            if heading in {'condition','cond','cond.'}:
                state = {'NEW':'NEW','NE':'NEW','FN':'FACTORY_NEW','NS':'NEW_SURPLUS','USED':'USED','REFURBISHED':'REFURBISHED','OH':'OVERHAULED','SV':'SERVICEABLE','SVC':'SERVICEABLE','AR':'AS_REMOVED','RP':'REPAIRED','US':'UNSERVICEABLE'}.get(value.upper())
                if state:
                    facts['condition'] = state
            if heading in {'country','country of dispatch','ships from','ship from'} and re.fullmatch(r'[A-Za-z .-]{2,60}', value):
                facts['country'] = value
        matches.append(facts)
    facts = {k:v for k,v in matches[0].items() if all(x.get(k) == v for x in matches)} if matches else {}
    visible = ' '.join(parser.visible)
    if matches and re.search(r'\b(?:no longer available|listing (?:has )?ended|auction closed|this item has been sold)\b', visible, re.I):
        facts['availability'] = 'SOURCE_OUT_OF_STOCK'
    return facts


def offer_facts(page, model):
    parser = StructuredData()
    parser.feed(page[:500000])
    def walk(value):
        if isinstance(value, list):
            for child in value:
                yield from walk(child)
        elif isinstance(value, dict):
            yield value
            for key in ('@graph', 'mainEntity'):
                yield from walk(value.get(key))
    compact = lambda value: re.sub(r'[^a-z0-9]', '', str(value).lower())
    target = compact(model)
    found = []
    for block in parser.blocks:
        try:
            objects = list(walk(json.loads(block)))
        except (ValueError, TypeError, RecursionError):
            continue
        for product in objects:
            types = product.get('@type', [])
            if isinstance(types, str):
                types = [types.rsplit('/', 1)[-1]]
            if 'Product' not in types:
                continue
            identity = ' '.join(str(product.get(k) or '') for k in ('name', 'sku', 'mpn', 'model'))
            if not target or target not in compact(identity):
                continue
            offers = product.get('offers', [])
            if isinstance(offers, dict):
                offers = [offers]
            for offer in offers:
                if not isinstance(offer, dict) or offer.get('@type') == 'AggregateOffer':
                    continue
                facts = {}
                condition = str(offer.get('itemCondition') or product.get('itemCondition') or '').rsplit('/', 1)[-1]
                if condition in {'NewCondition', 'UsedCondition', 'RefurbishedCondition', 'DamagedCondition'}:
                    facts['condition'] = {'NewCondition':'NEW','UsedCondition':'USED','RefurbishedCondition':'REFURBISHED','DamagedCondition':'FOR_PARTS'}[condition]
                availability = str(offer.get('availability') or '').rsplit('/', 1)[-1]
                if availability in {'InStock','OutOfStock','PreOrder','BackOrder','SoldOut','Discontinued'}:
                    facts['availability'] = {'InStock':'SOURCE_IN_STOCK','OutOfStock':'SOURCE_OUT_OF_STOCK','PreOrder':'SOURCE_PREORDER','BackOrder':'SOURCE_BACKORDER','SoldOut':'SOURCE_OUT_OF_STOCK','Discontinued':'SOURCE_DISCONTINUED'}[availability]
                shipping = offer.get('shippingDetails', {})
                if isinstance(shipping, list):
                    shipping = shipping[0] if len(shipping) == 1 else {}
                origin = shipping.get('shippingOrigin', {}) if isinstance(shipping, dict) else {}
                country = origin.get('addressCountry') if isinstance(origin, dict) else None
                if isinstance(country, str) and re.fullmatch('[A-Z]{2}', country):
                    facts['country'] = country
                spec = offer.get('priceSpecification', {})
                unit = spec.get('referenceQuantity', {}) if isinstance(spec, dict) else {}
                if isinstance(unit, dict) and unit.get('unitCode') in {'C62','H87','SET','KGM','MTR'} and unit.get('value') == 1:
                    facts['price_unit'] = unit['unitCode']
                found.append(facts)
    # Conflicting variants must not be collapsed into a single asserted offer.
    structured = {key:value for key,value in found[0].items() if all(row.get(key) == value for row in found)} if found else {}
    tables = table_facts(page, model)
    for key, value in tables.items():
        if key in structured and structured[key] != value:
            structured.pop(key)
        else:
            structured[key] = value
    return structured
