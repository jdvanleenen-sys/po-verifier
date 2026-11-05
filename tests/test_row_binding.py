"""Each row's figures are read from that row, inside its own PO's block. Run from the repo root:

    python -m unittest discover -s tests -v

A peer test found the hole this closes: a row printed +$999.00 where the variance says +$220.00
passed, because the right +$220.00 was printed on the subtotal line under it. Each planted mistake
below must fail; each clean version must pass. Rows are laid out the way the real PDF reads (one
cell per line: item, unit, agreed rate, PO qty, PO rate, PO amount, measured qty, measured value,
difference, why). The last test runs on the committed 77 Mockup Drive PDF.
"""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import verify  # noqa: E402

PO_A, PO_B = "MKR-02402431/027", "MKR-02402431/041"
HEADINGS = "ITEM\nUNIT\nAGREED RATE\nPO QTY\nPO RATE\nPO AMOUNT\nMEASURED QTY\nMEASURED VALUE\nDIFFERENCE\nWHY\n"


def row(item, rate, po_qty, po_amount, qty, value, diff):
    """One expected row and its printed cells."""
    expected = {"item": item, "rate": D(rate), "po_amount": D(po_amount),
                "measured_value": D(value), "difference": D(diff)}
    sign = "+" if D(diff) >= 0 else "-"
    cells = [item, "EA", f"${rate}", po_qty, f"${rate}", f"${po_amount}", qty, f"${value}",
             f"{sign}${abs(D(diff)):.2f}", "Short of the site count."]
    return expected, cells


DOORS = row("8' doors and trim", "60.00", "7", "420.00", "12", "720.00", "300.00")
DOORS_SHORT = row("8' doors", "55.00", "2", "110.00", "6", "330.00", "220.00")
RAIL = row("Stain railing", "12.00", "16", "192.00", "19", "228.00", "36.00")


def block(po, rows, subtotal):
    """One PO group block: heading, column headings, rows, subtotal, tax, total."""
    body = "".join("\n".join(cells) + "\n" for _, cells in rows)
    tax = (D(subtotal) * D("0.05")).quantize(D("0.01"))
    return (f"PO {po} Interior paint and stain. One EPO for this PO.\n" + HEADINGS + body +
            f"Difference before tax\n+${subtotal}\nGST/HST 5%, from this PO's own tax line\n${tax}\n"
            f"EPO requested for this PO\n${D(subtotal) + tax}\n")


def expected(groups):
    """groups: [(po, [row, ...])] -> the expected request, as money.expected_request() gives it."""
    out = {"rows_on": [], "rows_off": [], "groups": {}}
    for po, rows in groups:
        before = sum((r[0]["difference"] for r in rows), D(0))
        tax = (before * D("0.05")).quantize(D("0.01"))
        out["groups"][po] = {"before": before, "tax": tax, "total": before + tax}
        out["rows_on"] += [{"po": po, **r[0]} for r in rows]
    return out


def passes(result):
    return ": pass:" in result


def edit(cells_row, index, value):
    """A copy of one row with one printed cell changed."""
    cells = list(cells_row[1])
    cells[index] = value
    return cells_row[0], cells


class RowBoundDifferences(unittest.TestCase):
    def check(self, text, exp):
        return verify.check_differences(text, exp)

    def test_clean_two_row_group_passes(self):
        exp = expected([(PO_A, [DOORS, RAIL])])
        result = self.check(block(PO_A, [DOORS, RAIL], "336.00"), exp)
        self.assertTrue(passes(result), result)

    def test_wrong_row_difference_with_right_subtotal_fails(self):
        """The peer test's attack: one row's difference changed, the subtotal left right."""
        exp = expected([(PO_A, [DOORS])])
        text = block(PO_A, [edit(DOORS, 8, "+$999.00")], "300.00")
        result = self.check(text, exp)
        self.assertFalse(passes(result))
        self.assertIn("+999.00", result)

    def test_two_rows_with_their_differences_swapped_fails(self):
        exp = expected([(PO_A, [DOORS, RAIL])])
        text = block(PO_A, [edit(DOORS, 8, "+$36.00"), edit(RAIL, 8, "+$300.00")], "336.00")
        self.assertFalse(passes(self.check(text, exp)))

    def test_difference_printed_without_its_sign_fails(self):
        exp = expected([(PO_A, [DOORS])])
        text = block(PO_A, [edit(DOORS, 8, "$300.00")], "300.00")
        self.assertFalse(passes(self.check(text, exp)))

    def test_wrong_po_amount_measured_value_or_rate_on_the_row_fails(self):
        exp = expected([(PO_A, [DOORS])])
        for index, value in ((5, "$480.00"), (7, "$780.00"), (2, "$65.00")):
            with self.subTest(cell=index):
                result = self.check(block(PO_A, [edit(DOORS, index, value)], "300.00"), exp)
                self.assertFalse(passes(result), result)

    def test_same_item_under_two_pos_is_read_from_each_block(self):
        rail_b = row("Stain railing", "12.00", "10", "120.00", "15", "180.00", "60.00")
        exp = expected([(PO_A, [RAIL]), (PO_B, [rail_b])])
        clean = block(PO_A, [RAIL], "36.00") + block(PO_B, [rail_b], "60.00")
        self.assertTrue(passes(self.check(clean, exp)), self.check(clean, exp))
        crossed = block(PO_A, [edit(RAIL, 8, "+$60.00")], "36.00") + block(PO_B, [edit(rail_b, 8, "+$36.00")], "60.00")
        self.assertFalse(passes(self.check(crossed, exp)))

    def test_a_row_printed_under_the_wrong_po_fails(self):
        exp = expected([(PO_A, [DOORS]), (PO_B, [RAIL])])
        text = block(PO_A, [DOORS, RAIL], "336.00") + block(PO_B, [], "0.00")
        self.assertFalse(passes(self.check(text, exp)))

    def test_short_name_inside_a_longer_name_is_its_own_row(self):
        """'8' doors' is part of '8' doors and trim'; each must be read from its own row."""
        exp = expected([(PO_A, [DOORS, DOORS_SHORT])])
        clean = block(PO_A, [DOORS, DOORS_SHORT], "520.00")
        self.assertTrue(passes(self.check(clean, exp)), self.check(clean, exp))
        wrong = block(PO_A, [DOORS, edit(DOORS_SHORT, 8, "+$300.00")], "520.00")
        self.assertFalse(passes(self.check(wrong, exp)))

    def test_po_heading_printed_twice_fails(self):
        exp = expected([(PO_A, [DOORS])])
        text = block(PO_A, [DOORS], "300.00") + block(PO_A, [DOORS], "300.00")
        self.assertFalse(passes(self.check(text, exp)))


class GroupSubtotal(unittest.TestCase):
    def test_wrong_subtotal_with_right_tax_and_total_fails(self):
        exp = expected([(PO_A, [DOORS])])
        clean = block(PO_A, [DOORS], "300.00")
        self.assertTrue(passes(verify.check_tax(clean, exp)), verify.check_tax(clean, exp))
        wrong = clean.replace("Difference before tax\n+$300.00", "Difference before tax\n+$900.00")
        self.assertFalse(passes(verify.check_tax(wrong, exp)))


class CommittedSamplePdf(unittest.TestCase):
    """The committed 77 Mockup Drive request, as Chrome printed it."""
    PDF = ROOT / "05 request" / "77-mockup-drive" / "vpo-request-1.pdf"
    EXP = {"rows_on": [
        {"po": "MKR-02402401/027", "item": "8' doors and trim", "rate": D("60.00"), "po_amount": D("420.00"),
         "measured_value": D("720.00"), "difference": D("300.00")},
        {"po": "none", "item": "Prime and paint garage, including ceiling", "rate": D("1.60"),
         "po_amount": D("0"), "measured_value": D("672.00"), "difference": D("672.00")}],
        "rows_off": [],
        "groups": {"MKR-02402401/027": {"before": D("300"), "tax": D("15.00"), "total": D("315.00")},
                   "none": {"before": D("672"), "tax": D("33.60"), "total": D("705.60")}}}

    def request(self):
        return " ".join(verify.split_request(verify.pdf_pages(self.PDF))[0])

    def test_sample_passes(self):
        text = self.request()
        for check in (verify.check_differences, verify.check_tax):
            self.assertTrue(passes(check(text, self.EXP)), check(text, self.EXP))

    def test_sample_with_the_row_changed_fails(self):
        text = self.request()
        self.assertEqual(text.count("+$300.00"), 2)  # the row, then the subtotal under it
        attacked = text.replace("+$300.00", "+$999.00", 1)
        self.assertFalse(passes(verify.check_differences(attacked, self.EXP)))
        self.assertTrue(passes(verify.check_tax(attacked, self.EXP)))  # the subtotal alone still holds


if __name__ == "__main__":
    unittest.main()
