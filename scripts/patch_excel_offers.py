"""Fail-closed candidates for the inspected staging attachment/public handlers."""
from pathlib import Path
import sys


def patch_attachment(text):
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('ATTACHMENT_SOURCE_MISMATCH: ' + old)
        text = text.replace(old, new, 1)
    replace("    content = [{'type': 'input_text', 'text': prompt}]", """    from .document_offers import document_parts, validate_document_output
    parts = document_parts(attachment.get('text', ''))
    if len(parts) > 1:
        prompt += (' This is a multi-item procurement document, not one product. '
                   'Research commercial item listings separately for each exact P/N in this list: '
                   + ', '.join(parts) + '. Each candidate must identify its own exact P/N and manufacturer. '
                   'Use your web-search budget for supplier listings, not only OEM specifications. '
                   'Include independently cited product offers when available, preserve every suffix, '
                   'and report coverage gaps honestly. Never require one seller page to contain all parts. ')
    content = [{'type': 'input_text', 'text': prompt}]""")
    replace('    if not exact:', '    if not exact and not parts:')
    replace('    report = validate_output(data, key, locale)', "    report = validate_document_output(data, key, locale, attachment.get('text', ''))")
    return text


def patch_gateway(text):
    old = "        for field in ('seller_country','dispatch_country','manufacturing_country','price_unit'):"
    if text.count(old) != 1:
        raise ValueError('GATEWAY_SOURCE_MISMATCH')
    return text.replace(old, "        for field in ('seller_country','dispatch_country','manufacturing_country','price_unit','part_number','product_name'):", 1)


if __name__ == '__main__':
    path = Path(sys.argv[1])
    fn = patch_attachment if path.name == 'attachment_search.py' else patch_gateway if path.name == 'pilot_gateway.py' else None
    if fn is None:
        raise SystemExit('UNEXPECTED_TARGET')
    candidate = fn(path.read_text('utf-8'))
    compile(candidate, str(path), 'exec')
    path.with_name(path.name + '.excel.new').write_text(candidate, 'utf-8')
    print('CANDIDATE_READY', path.name)
