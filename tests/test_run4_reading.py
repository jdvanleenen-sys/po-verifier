"""Loop run 4 on a real house, 2026-11-09: two reading gaps the attacker got money through. Run from
the repo root: python -m unittest discover -s tests -v

1. a20: a read-back row with its qty and unit price swapped (125 x 2.00 for 2 x 125.00, same total)
   passed the po-line rule, which only checked the three numbers were somewhere on the PO line.
2. a10/a11/a15: the size slot was never set against Sam's own quoted words, so "Railing 16'" with 61
   in the slot, a range ("13-14'") or a pointer ("see row 3") passed as a size.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "02 read")]
import grid_rules as rules  # noqa: E402
import po_lines  # noqa: E402

HOUSE = ROOT / "tests" / "houses" / "40-larch-crescent" / "intake"
PO = "MKR-02402440/027"
DOORS = "09900/030S - 8' Doors & Trim"


def read_back(*rows):
    head = ("## Rows\n| # | PO number | Line as printed | Unit as printed | PO qty | Unit price | Line total |\n"
            "|---|---|---|---|---|---|---|\n")
    return head + "".join(f"| {n} | {po} | {line} | EA | {q} | {p} | {t} |\n" for n, po, line, q, p, t in rows)


def row(said, po_qty="16"):
    return {"#": "2", "po number": "A-1/094", "po qty": po_qty, "unit price": "40.00",
            "line total": str(int(po_qty) * 40) + ".00", "price list item": "Railing",
            "sam measured (his words)": said}


class PoLineOrder(unittest.TestCase):
    def test_qty_and_price_swapped_fails(self):
        problems, _ = po_lines.check(HOUSE, read_back(("1", PO, DOORS, "60", "$12.00", "$720.00")))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("12 x 60 = 720", problems[0])

    def test_qty_price_total_in_order_passes(self):
        self.assertEqual(po_lines.check(HOUSE, read_back(("1", PO, DOORS, "12", "$60.00", "$720.00"))), ([], 0))

    def test_in_order_allows_numbers_between(self):
        self.assertTrue(po_lines.in_order([5120, 12, 1, 60, 720], [12, 60, 720]))
        self.assertFalse(po_lines.in_order([12, 60, 720], [60, 12, 720]))


class SlotMatchesHisWords(unittest.TestCase):
    def test_slot_that_is_not_his_number_asks_sam(self):
        for said in ('"Railing 16\'"; 61 ft', '"Railing 13-14\'"; 13 ft', '"Railing 13 to 14\'"; 13 ft',
                     '"Railing 16\' (see row 3)"; 14 ft', '"Handrail, same as the railing"; 16 ft',
                     '"Railing 16\' row 3"; 16 ft'):
            with self.subTest(said=said):
                self.assertIsNone(rules.measured_qty(row(said)))
                self.assertTrue(rules.measured(row(said), {}).startswith(rules.ASK_SAM))

    def test_his_number_or_no_number_still_reads(self):
        for said, want in (('"Railing 16\'"; 16 ft', "16"), ('"done as ordered"; 16; standing answer', "16"),
                           ('"8\' doors 12"; count 12', "12"), ('"2,152 sf"; 2152', "2152"),
                           ('"3.016 sf"; 3016, Sam confirmed 3016', "3016")):
            with self.subTest(said=said):
                self.assertEqual(str(rules.measured_qty(row(said))), want)


if __name__ == "__main__":
    unittest.main()
