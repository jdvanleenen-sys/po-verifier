"""The price list is an Excel file, reference/price-list.xlsx. Run from the repo root:

    python -m unittest discover -s tests -v

Jeff, 2026-11-08: the price list moves out of Airtable into an Excel file in the folder, and that is
how it runs from now on. The checker reads the 'Price list' sheet (Item, Unit, Rate, Active; any
other column, such as Source, is ignored) and freezes a plain CSV copy per house, as before.
"""
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import prices  # noqa: E402


def workbook(path, rows, header=("Item", "Unit", "Rate", "Active", "Source"), sheet="Price list"):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(list(header))
    for r in rows:
        ws.append(list(r))
    wb.save(path)
    return path


class ExcelPriceList(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def read(self, *rows, **kw):
        path = workbook(self.dir / "price-list.xlsx", rows, **kw)
        return prices.parse(prices.source_bytes(path))

    def test_the_repo_price_list_is_excel_and_clean(self):
        rows, problems = prices.parse(prices.source_bytes())
        self.assertEqual(problems, [])
        self.assertGreater(len(rows), 0)

    def test_rates_units_and_active_come_through(self):
        rows, problems = self.read(("Handrail", "LF", 8.25, True, "Airtable"), ("Old item", "EA", 10, False, ""))
        self.assertEqual(problems, [])
        self.assertEqual(str(rows["handrail"]["rate"]), "8.25")
        self.assertEqual(rows["handrail"]["unit"], "LF")
        self.assertFalse(rows["old item"]["active"])

    def test_source_column_is_ignored(self):
        rows, problems = self.read(("Handrail", "LF", 8.25, True, "anything at all, 1,2,3"))
        self.assertEqual(problems, [])
        self.assertEqual(len(rows), 1)

    def test_a_float_rate_does_not_pick_up_noise(self):
        rows, _ = self.read(("Basic SF", "Floor SF", 2.9, True, ""))
        self.assertEqual(str(rows["basic sf"]["rate"]), "2.9")

    def test_a_text_rate_is_refused(self):
        _, problems = self.read(("Handrail", "LF", "eight", True, ""))
        self.assertTrue(any("not a number" in p for p in problems), problems)

    def test_wrong_columns_are_refused(self):
        _, problems = self.read(("Handrail", 8.25, "LF", True), header=("Item", "Rate", "Unit", "Active"))
        self.assertTrue(any("Item, Unit, Rate, Active" in p for p in problems), problems)

    def test_missing_sheet_is_refused_in_plain_words(self):
        path = workbook(self.dir / "price-list.xlsx", [("Handrail", "LF", 8.25, True)], sheet="Sheet1")
        with self.assertRaises(SystemExit) as stop:
            prices.source_bytes(path)
        self.assertIn("Price list", str(stop.exception))

    def test_missing_file_is_refused_in_plain_words(self):
        with self.assertRaises(SystemExit) as stop:
            prices.source_bytes(self.dir / "nothing.xlsx")
        self.assertIn("price list", str(stop.exception).lower())

    def test_same_workbook_gives_the_same_fingerprint(self):
        path = workbook(self.dir / "price-list.xlsx", [("Handrail", "LF", 8.25, True, "x")])
        self.assertEqual(prices.fingerprint(prices.source_bytes(path)), prices.fingerprint(prices.source_bytes(path)))


if __name__ == "__main__":
    unittest.main()
