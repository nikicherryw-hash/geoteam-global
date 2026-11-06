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
    if not found:
        return {}
    return {key:value for key,value in found[0].items() if all(row.get(key) == value for row in found)}
