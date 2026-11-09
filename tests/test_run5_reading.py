"""Loop run 5 on a real house, 2026-11-09: what got past the reader. Run from the repo root:

    python -m unittest discover -s tests -v

1. A price list rate typed "2,900" (meaning 2.90) was read as $2,900.
2. Sam's quoted words were not read for the traps the slot is read for: "sixteen feet", "16 ft 6 in",
   "ditto", "2 @ 8'", and words with no number at all backed any slot.
3. A row whose PO number was mistyped (a 0 missing) was counted as "on a PDF PO, check by eye"
   instead of failing.
"""
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import grid_rules as rules  # noqa: E402
import po_lines  # noqa: E402
import prices  # noqa: E402


def row(said):
    return {"#": "8", "po number": "A-1/065", "po qty": "15", "unit price": "40.00", "line total": "600.00",
            "price list item": "Railing", "sam measured (his words)": said}


class RateWithAComma(unittest.TestCase):
    def test_a_comma_with_no_cents_is_refused_by_name(self):
        raw = 'Item,Unit,Rate,Active\nBasic painting,Floor SF,"2,900",TRUE\n'.encode()
        _, problems = prices.parse(raw)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("Basic painting", problems[0])
        self.assertIn("2900 or 2.90", problems[0])

    def test_thousands_with_cents_still_read(self):
        self.assertEqual(prices.to_rate("$1,000.00"), Decimal("1000.00"))
        self.assertEqual(prices.to_rate("2.90"), Decimal("2.90"))


class QuotedWordsAreReadForTraps(unittest.TestCase):
    def test_traps_in_his_words_ask_sam(self):
        for said in ('"Railing sixteen feet"; 61 ft', '"Railing 16 ft 6 in"; 16 ft', "\"Railing 16'6\\\"\"; 16 ft",
                     '"Railing ditto handrail"; 14 ft', '"Railing as above"; 16 ft', "\"Railing 2 @ 8'\"; 8 ft",
                     "\"Railing 8' times 2\"; 8 ft", "\"Railing 8' (2)\"; 8 ft", "\"Railing 2 of 8'\"; 8 ft",
                     '"railing"; 16 ft'):
            with self.subTest(said=said):
                self.assertIsNone(rules.measured_qty(row(said)))

    def test_plain_words_still_read(self):
        for said, want in (("\"Railing 16'\"; 16 ft; no colour given", "16"),
                           ('"done as ordered"; 15; standing answer, contractor.md', "15"),
                           ("\"8' doors x12\"; count 12", "12"), ("stringers; 34 ft", "34"),
                           ('"GARAGE 420 sf. said a change order was coming, never saw one."; 420 sf', "420")):
            with self.subTest(said=said):
                self.assertEqual(rules.measured_qty(row(said)), Decimal(want))


PO = """<html><body><p>ORDER #: A-1/065</p><table>
<tr><td>(1) 60100/020S - Interior Railing</td><td>EA</td><td>15</td><td>$40.00</td><td>$600.00</td></tr>
</table></body></html>"""
READ_BACK = """## Rows
| # | PO number | Line as printed | Unit as printed | PO qty | Unit price | Line total |
|---|---|---|---|---|---|---|
| 8 | {po} | (1) 60100/020S - Interior Railing | EA | 15 | $40.00 | $600.00 |
"""


class PoNumberMustBeAnIntakePo(unittest.TestCase):
    def check(self, po):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "po-065.html").write_text(PO, encoding="utf-8")
            return po_lines.check(Path(d), READ_BACK.format(po=po))

    def test_a_mistyped_po_number_fails(self):
        problems, unchecked = self.check("A-1/0065")
        self.assertEqual(unchecked, 0)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("not the ORDER # of any PO", problems[0])

    def test_the_right_po_number_passes(self):
        self.assertEqual(self.check("A-1/065"), ([], 0))


if __name__ == "__main__":
    unittest.main()
