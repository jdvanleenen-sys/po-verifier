"""Two traps the AI caught in the 2026-11-04 loop, now caught by code. Run from the repo root:

    python -m unittest discover -s tests -v

1. A measured number that is probably the PO's number written with a dot for a comma ("3.016" for
   3,016), or ten times off the PO, or a zero against a PO line. Code asks Sam before it is priced.
2. The same item, quantity and price on two different POs: probably ordered twice. Code asks Sam.
Both stop asking once the row says "Sam confirmed". No browser needed.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import grid_rules as rules  # noqa: E402

ITEM = "8' doors and trim"


def row(po, qty, said, item=ITEM, price="60.00"):
    return {"#": "1", "po number": po, "po qty": qty, "unit price": price, "line total": "",
            "price list item": item, "sam measured (his words)": said}


def status(cell):
    return cell.split(":", 1)[0]


class MeasuredScale(unittest.TestCase):
    def test_dot_for_a_comma_asks_sam(self):
        cell = rules.measured(row("A-1/027", "3016", '"3.016 sf"; 3.016', "Basic SF Painting"), {})
        self.assertEqual(status(cell), rules.ASK_SAM, cell)
        self.assertIn("comma", cell)

    def test_ten_times_off_asks_sam(self):
        cell = rules.measured(row("A-1/027", "15", '"railing 150"; 150'), {})
        self.assertEqual(status(cell), rules.ASK_SAM, cell)

    def test_zero_against_a_po_line_asks_sam(self):
        cell = rules.measured(row("A-1/033", "12", '"8\' doors 12"; 0 here, counted on /027'), {})
        self.assertEqual(status(cell), rules.ASK_SAM, cell)

    def test_half_foot_is_fine(self):
        cell = rules.measured(row("A-1/027", "22", '"railing wood 22.5 ft"; 22.5'), {})
        self.assertEqual(status(cell), rules.PASS, cell)

    def test_sam_confirmed_clears_it(self):
        cell = rules.measured(row("A-1/027", "3016", '"3.016 sf"; 3016, Sam confirmed', "Basic SF Painting"), {})
        self.assertEqual(status(cell), rules.PASS, cell)
        cell = rules.measured(row("A-1/033", "12", '"8\' doors 12"; 0 here, counted on /027, Sam confirmed'), {})
        self.assertEqual(status(cell), rules.PASS, cell)

    def test_no_po_row_has_nothing_to_compare(self):
        cell = rules.measured(row("none", "", '"furnace rm floor 1"; 1', "Furnace room floor"), {})
        self.assertEqual(status(cell), rules.PASS, cell)


class OrderedTwice(unittest.TestCase):
    def house(self, *rows):
        return {"rows": list(rows)}

    def test_same_item_qty_price_on_two_pos_asks_sam(self):
        a, b = row("A-1/027", "12", '"8\' doors 12"'), row("A-1/033", "12", '"8\' doors 12"; 0')
        cell = rules.count(b, self.house(a, b))
        self.assertEqual(status(cell), rules.ASK_SAM, cell)
        self.assertIn("A-1/027", cell)

    def test_different_qty_is_not_flagged(self):
        a, b = row("A-1/027", "12", '"8\' doors 12"'), row("A-1/033", "2", '"8\' doors 2"')
        self.assertEqual(rules.count(b, self.house(a, b)), rules.ASK)

    def test_sam_confirmed_clears_it(self):
        a = row("A-1/027", "12", '"8\' doors 12"')
        b = row("A-1/033", "12", '"8\' doors 12" counted on /027; 0, Sam confirmed')
        self.assertEqual(rules.count(b, self.house(a, b)), rules.ASK)


if __name__ == "__main__":
    unittest.main()
