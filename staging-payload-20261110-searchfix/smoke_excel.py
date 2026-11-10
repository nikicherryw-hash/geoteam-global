import io
import zipfile
from sourcing.search_v2.batch_document import extract_list_items
from sourcing.search_v2.office_extract import XLSX

def sheet(rows):
    body = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
    for row in rows:
        body += '<row>' + ''.join('<c t="inlineStr"><is><t>' + cell + '</t></is></c>' for cell in row) + '</row>'
    body += '</sheetData></worksheet>'
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as archive:
        archive.writestr('xl/worksheets/sheet1.xml', body)
    return out.getvalue()

named = extract_list_items(sheet([['Наименование товара'], ['ROTAX 912 engine'], ['Siemens motor']]), XLSX)
assert len(named) == 2 and all('part_number' not in item for item in named), named
parts = extract_list_items(sheet([['P/N','Manufacturer'], ['5SY6106-7','Siemens']]), XLSX)
assert parts[0]['part_number'] == '5SY6106-7', parts
print('EXCEL_PARSER_OK', len(named), len(parts))
