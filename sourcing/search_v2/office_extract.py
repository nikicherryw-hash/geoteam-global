"""Bounded text extraction from Office Open XML, without executing macros."""
import io
import zipfile
import xml.etree.ElementTree as ET

DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def extract_office(data, mime):
    if mime not in {DOCX, XLSX}:
        raise ValueError('UNSUPPORTED_OFFICE_FORMAT')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if len(members) > 2000 or sum(x.file_size for x in members) > 40 * 1024 * 1024:
            raise ValueError('OFFICE_EXPANSION_LIMIT')
        if any(x.flag_bits & 1 for x in members):
            raise ValueError('PASSWORD_PROTECTED_FILE')
        def xml(name):
            content = archive.read(name)
            if b'<!DOCTYPE' in content or b'<!ENTITY' in content:
                raise ValueError('INVALID_XML')
            return ET.fromstring(content)
        rows = []
        if mime == DOCX:
            root = xml('word/document.xml')
            ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            rows = [''.join(p.itertext()) for p in root.iter(ns + 'p')]
        else:
            ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
            shared = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                shared = [''.join(si.itertext()) for si in xml('xl/sharedStrings.xml').iter(ns + 'si')]
            for name in sorted(archive.namelist()):
                if not (name.startswith('xl/worksheets/sheet') and name.endswith('.xml')):
                    continue
                for row in xml(name).iter(ns + 'row'):
                    values = []
                    for cell in row.findall(ns + 'c'):
                        value = cell.findtext(ns + 'v', '')
                        if cell.get('t') == 's':
                            value = shared[int(value)]
                        elif cell.get('t') == 'inlineStr':
                            value = ''.join(cell.itertext())
                        values.append(value)
                    rows.append('\t'.join(values))
        text = '\n'.join(x for x in rows if x.strip())
        if not text.strip():
            raise ValueError('EMPTY_OFFICE_FILE')
        if len(text) > 100000:
            raise ValueError('DOCUMENT_TEXT_LIMIT')
        return text
