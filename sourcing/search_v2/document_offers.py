"""Validate offers against individual identifiers actually present in a document."""
import copy
import json
import re
from .ai_search import public_offer_id, validate_output
from .matching import model_matches


def document_parts(text, maximum=50):
    # Part codes only, not quantities, voltages or descriptive document titles.
    # Office exports commonly embed a P/N in a filename-style cell such as
    # ``item_5SY6106-7_Siemens``.  An underscore is a ``\w`` character in
    # Python regexes, so normalise it to a boundary before extracting codes.
    # This does not relax matching: each resulting P/N is still checked against
    # the cited candidate's model and optional declared part number.
    normalized = str(text or '').replace('_', ' ')
    tokens = re.findall(r'(?<!\w)[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)+(?!\w)', normalized)
    result = []
    for token in tokens:
        if len(token) < 5 or not any(c.isalpha() for c in token) or not any(c.isdigit() for c in token):
            continue
        token = token.upper()
        if token not in result:
            result.append(token)
    if len(result) > maximum:
        raise ValueError('DOCUMENT_ITEM_LIMIT')
    return result


def validate_document_output(data, query, locale, document_text):
    parts = document_parts(document_text)
    if not parts:
        return validate_output(data, query, locale)
    messages = [block for item in data.get('output', []) if item.get('type') == 'message'
                for block in item.get('content', []) if block.get('type') == 'output_text']
    raw = json.loads(''.join(block['text'] for block in messages))
    manufacturer = str((raw.get('product') or {}).get('manufacturer') or '').strip()
    manufacturer = manufacturer if manufacturer and model_matches(manufacturer, document_text) else ''
    base = validate_output(data, query, locale)
    base['offers'], base['_internal_sources'] = [], []
    for part in parts:
        candidates = []
        for candidate in raw.get('candidates', [])[:100]:
            if not isinstance(candidate, dict):
                continue
            # Both declared model and optional explicit P/N must agree.
            if not model_matches(part, candidate.get('model', '')):
                continue
            if candidate.get('part_number') and not model_matches(part, candidate['part_number']):
                continue
            if manufacturer and not model_matches(manufacturer, str(candidate.get('model','')) + ' ' + str(candidate.get('product_name',''))):
                continue
            candidates.append(candidate)
        report = dict(raw, candidates=candidates)
        envelope = copy.deepcopy(data)
        blocks = [b for item in envelope.get('output', []) if item.get('type') == 'message'
                  for b in item.get('content', []) if b.get('type') == 'output_text']
        blocks[0]['text'] = json.dumps(report)
        for block in blocks[1:]:
            block['text'] = ''
        validated = validate_output(envelope, part, locale)
        seen = set()
        for offer, lead in zip(validated['offers'], validated['_internal_sources']):
            url = lead['source_url']
            if url in seen:
                continue
            seen.add(url)
            public_id = public_offer_id(url, len(base['offers']) + 1)
            offer.update(public_offer_id=public_id, part_number=part, product_name=part)
            lead.update(public_offer_id=public_id, requested_part_number=part)
            base['offers'].append(offer)
            base['_internal_sources'].append(lead)
    base['warnings'].append('DOCUMENT_POSITIONS_VALIDATED_INDIVIDUALLY')
    base['document_item_count'] = len(parts)
    base['document_candidate_count'] = len(raw.get('candidates', []))
    return base
