"""Prepare a guarded candidate for the audited staging attachment handler."""
from pathlib import Path
import sys


def main():
    path = Path(sys.argv[1])
    text = path.read_text(encoding='utf-8')
    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise SystemExit('REFUSED_MARKER: ' + old[:70])
        text = text.replace(old, new, 1)
    replace('def decode_attachment(obj):', '''def decode_attachment(obj):
    from .office_extract import DOCX, XLSX, extract_office
    if isinstance(obj, dict) and obj.get('mime') in {DOCX, XLSX}:
        raw = base64.b64decode(obj.get('data', ''), validate=True)
        if not raw or len(raw) > MAX_ATTACHMENT_BYTES:
            raise ValueError('ATTACHMENT_TOO_LARGE')
        return {'mime': 'text/plain', 'filename': 'office.txt', 'text': extract_office(raw, obj['mime'])}
    return _decode_attachment_original(obj)


def _decode_attachment_original(obj):''')
    replace("'max_output_tokens': 1800", "'max_output_tokens': 12000")
    replace("parsed = json.loads(texts[0])", "parsed = json.loads(''.join(texts))")
    replace("    report['usage'] = data.get('usage', {})", """    from .ai_search import attach_source_images, _product_card
    await attach_source_images(report['_internal_sources'])
    image = next((x.get('image_url') for x in report['_internal_sources'] if x.get('image_url')), None)
    report['product'] = _product_card(report.pop('_report'), key, report['citations_returned'], bool(image))
    report['image'] = None
    report['_representative_image_url'] = image
    report['usage'] = data.get('usage', {})""")
    path.with_name(path.name + '.new').write_text(text, encoding='utf-8')
    print('CANDIDATE_READY')


if __name__ == '__main__':
    main()
