import io
import unittest
import zipfile

from .batch_document import extract_list_items
from .office_extract import XLSX


class BatchDocumentTests(unittest.TestCase):
    def test_csv_keeps_distinct_rows_and_manufacturers(self):
        source = "Part Number;Manufacturer;Description\n915 iS;BRP-Rotax;Aircraft engine\nXPSUDN13AP;Schneider;Safety relay\n"
        items = extract_list_items(source.encode(), "text/csv")
        self.assertEqual([item["part_number"] for item in items], ["915 iS", "XPSUDN13AP"])
        self.assertEqual(items[1]["manufacturer"], "Schneider")

    def test_excel_uses_existing_bounded_extractor(self):
        sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
                 '<row><c t="inlineStr"><is><t>P/N</t></is></c><c t="inlineStr"><is><t>Manufacturer</t></is></c></row>'
                 '<row><c t="inlineStr"><is><t>5SY6106-7</t></is></c><c t="inlineStr"><is><t>Siemens</t></is></c></row>'
                 '</sheetData></worksheet>')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("xl/worksheets/sheet1.xml", sheet)
        self.assertEqual(extract_list_items(buffer.getvalue(), XLSX)[0]["part_number"], "5SY6106-7")

    def test_101_positions_are_rejected(self):
        source = "P/N\n" + "\n".join(f"PN-{i}" for i in range(101))
        with self.assertRaisesRegex(ValueError, "DOCUMENT_ITEM_LIMIT"):
            extract_list_items(source.encode(), "text/csv")

    def test_unstructured_file_requires_review(self):
        with self.assertRaisesRegex(ValueError, "PART_NUMBER_COLUMN_REQUIRED"):
            extract_list_items(b"Some machine, maybe 912", "text/plain")
        with self.assertRaisesRegex(ValueError, "DOCUMENT_REQUIRES_REVIEW"):
            extract_list_items(b"%PDF-1.4", "application/pdf")


if __name__ == "__main__":
    unittest.main()

