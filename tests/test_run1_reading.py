"""Group A of the 2026-11-09 attack on a real house: numbers and reading. Run from the repo root:

    python -m unittest discover -s tests -v

Each test names the attack it answers (a06 to a41). Made-up data only.
- a06/a41: a comma is a thousands separator only (1,234). "24,50" as a rate was read as 2450.
- a11 to a16: the size slot holds one plain number and a unit. Feet and inches, a multiplier, a
  range, a number in words or a pointer was read as a size (13'6" as 13, "124 ft x2" as 124,
  "ten" as the 12 in a source note, "see row 3" as 3 ft). Now each reads as no size: ask Sam.
- a03: the money gate took any number anywhere in Sam's cell as his measurement, so a 12 from a
  source note passed. It now reads the size exactly as the grid does.
"""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "02 read"), str(ROOT / "05 request")]
import grid_rules as rules  # noqa: E402
import money  # noqa: E402
import prices  # noqa: E402

NOTE = ' (photo, under "12 Sample Road", line 5)'


def row(said, po_qty="16"):
    return {"#": "3", "po number": "A-1/027", "po qty": po_qty, "unit price": "40.00", "line total": "640.00",
            "price list item": "Railing, wood", "sam measured (his words)": said}


class CommaIsThousandsOnly(unittest.TestCase):
    def test_comma_decimal_rate_is_refused_by_name(self):
        raw = "Item,Unit,Rate,Active\nMantle,LF,\"24,50\",TRUE\n".encode()
        rows, problems = prices.parse(raw)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("Mantle", problems[0])
        self.assertIn("comma", problems[0])

    def test_thousands_and_dollar_signs_still_read(self):
        self.assertEqual(prices.to_rate("$1,000.00"), Decimal("1000.00"))
        self.assertEqual(prices.to_rate("$40"), Decimal(40))
        self.assertEqual(rules.number("1,234,567.5"), Decimal("1234567.5"))

    def test_comma_decimal_cell_is_not_a_number(self):
        self.assertIsNone(rules.number("24,50"))


class SizeSlotIsOnePlainNumber(unittest.TestCase):
    def test_odd_sizes_read_as_nothing_and_ask_sam(self):
        for said in ('"Railing 13\'6""; 13\'6"; no colour', '"Railing 13 ft 6 in"; 13 ft 6 in; no colour',
                     '"Shelves 124\' x2"; 124 ft x2; no colour', '"Mantel 10-12\'"; 10-12 ft; no colour',
                     '"Mantel ten feet"; ten ft; no colour' + NOTE, '"Handrail, same as the railing"; see row 3; x',
                     '"Mantel 10,5\'"; 10,5 ft; no colour', '"Railing 13 to 14"; 13 to 14 ft'):
            with self.subTest(said=said):
                self.assertIsNone(rules.measured_text(row(said)))
                self.assertTrue(rules.measured(row(said), {}).startswith(rules.ASK_SAM))

    def test_plain_sizes_still_read(self):
        for said, want in (('"Railing 13\'"; 13 ft; no colour' + NOTE, "13"), ('"8\' doors x12"; count 12; no colour', "12"),
                           ('"done as ordered"; 2152; Sam confirmed', "2152"), ("stringers; 34 ft", "34"),
                           ('"8\' doors 12"; 0 here, counted on /027', "0"), ('"floor 2,152 sf"; 2,152 sf', "2,152"),
                           ('"railing 22.5\'"; 22.5\'', "22.5")):
            with self.subTest(said=said):
                self.assertEqual(rules.measured_text(row(said)), want)


class GateReadsTheSizeLikeTheGrid(unittest.TestCase):
    def check(self, qty):
        said = '"Fireplace mantel 10\'"; 10 ft; no colour given' + NOTE
        rb = {"rate": Decimal(24), "po": "none", "measured": said, "po_qty": None, "unit_price": None}
        v = {"item": "Mantle", "po": "none", "rate": Decimal(24), "po_qty": Decimal(0), "po_rate": None,
             "po_amount": Decimal(0), "measured_qty": Decimal(qty), "variance": Decimal(qty) * 24}
        problems = []
        money.checked_row(v, rb, [], problems)
        return problems

    def test_a_number_from_the_source_note_is_refused(self):
        self.assertTrue(any("not Sam's size" in p for p in self.check(12)), self.check(12))

    def test_the_size_itself_passes(self):
        self.assertEqual(self.check(10), [])


if __name__ == "__main__":
    unittest.main()
