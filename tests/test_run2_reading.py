"""Loop run 2 on a real house, 2026-11-09: what the attacker got past the reading and the printed
request. Made-up data only. Run from the repo root: python -m unittest discover -s tests -v

a16/a17/a18/a21/a24  a size slot with a tail ("124 ft (x2)", "13 – 14 ft", "13 ½ ft") read as one size
a12  two price rows differing only by the dash, both active, with different rates
a05  a headline total printed without cents ("$2,521") passed check 4
a06  a row's PO rate was never read off the PDF
a04  a tax line named GST on a PO that charges PST
"""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import grid_rules as rules  # noqa: E402
import prices  # noqa: E402
import request_text  # noqa: E402
import row_checks  # noqa: E402
import verify  # noqa: E402


def row(slot):
    return {"#": "2", "po number": "A-1/094", "po qty": "16", "unit price": "40.00", "line total": "640.00",
            "price list item": "Railing", "sam measured (his words)": f'"Railing words"; {slot}; no colour given'}


class SizeSlotIsAnAllowlist(unittest.TestCase):
    def test_a_tail_is_not_one_size(self):
        for slot in ("124 ft (x2)", "124 ft ×2", "13 – 14 ft", "13 ½ ft", "13 ft / 16 ft",
                     "13 ft x two", "13 ft by 2"):
            with self.subTest(slot=slot):
                self.assertIsNone(rules.measured_qty(row(slot)))

    def test_plain_sizes_and_remarks_still_read(self):
        for slot, want in (("13 ft", "13"), ("count 12", "12"), ("0 here, counted on /027", "0"),
                           ("3016, Sam confirmed", "3016"), ("2,152 sf", "2152"), ("22.5'", "22.5")):
            with self.subTest(slot=slot):
                self.assertEqual(rules.measured_qty(row(slot)), Decimal(want))


CSV = "Item,Unit,Rate,Active\n{a}\n{b}\n"


class NearDuplicatePriceRows(unittest.TestCase):
    def test_dash_twins_both_active_are_refused(self):
        raw = CSV.format(a='"Railing — wood, at the PO rate",LF,40,TRUE', b='"Railing - wood, at the PO rate",LF,60,TRUE')
        problems = prices.parse(raw.encode("utf-8"))[1]
        self.assertTrue(any("differ only by a dash" in p for p in problems), problems)

    def test_one_inactive_twin_is_fine(self):
        raw = CSV.format(a='"Railing — wood",LF,40,TRUE', b='"Railing - wood",LF,60,FALSE')
        self.assertEqual(prices.parse(raw.encode("utf-8"))[1], [])


class HeadlineAmounts(unittest.TestCase):
    def test_total_without_cents_is_not_read_past(self):
        text = "total requested $2,521 po a-1/094: $2,251.20"
        self.assertIsNone(request_text.first_amount_after(text, "total requested"))

    def test_total_with_cents_reads(self):
        self.assertEqual(request_text.first_amount_after("total requested $2,251.20 x", "total requested"),
                         Decimal("2251.20"))

    def test_amount_without_cents_is_named(self):
        self.assertEqual(len(verify.without_cents("TOTAL REQUESTED $2,521 and $2,251.20")), 1)


def printed(po_rate):
    return {"po": "A-1/094", "item": "railing", "rate": Decimal(40), "po_rate": po_rate, "po_qty": Decimal(16),
            "po_amount": Decimal(640), "measured_qty": Decimal(13), "measured_value": Decimal(520),
            "difference": Decimal(-120)}


class EveryCellOnTheRow(unittest.TestCase):
    def test_wrong_po_rate_is_refused(self):
        plain = [Decimal(40), Decimal(100), Decimal(640), Decimal(520)]
        problems = row_checks.row_problems(printed(Decimal(40)), plain, Decimal(-120), ["16", "", "13"])
        self.assertTrue(any("PO rate" in p for p in problems), problems)

    def test_no_po_row_with_a_po_rate_printed_is_refused(self):
        plain = [Decimal(40), Decimal(40), Decimal(640), Decimal(520)]
        problems = row_checks.row_problems(printed(None), plain, Decimal(-120), ["16", "", "13"])
        self.assertTrue(any("amount(s) before the difference" in p for p in problems), problems)


class TaxName(unittest.TestCase):
    expected = {"tax_names": {"a-1/094": {"pst"}}}

    def test_gst_on_a_pst_po_is_refused(self):
        key = request_text.normalise("A-1/094")
        self.assertTrue(verify.tax_name_problems(key, "gst 5%, from this po's own tax line", self.expected))

    def test_pst_passes(self):
        key = request_text.normalise("A-1/094")
        self.assertEqual(verify.tax_name_problems(key, "pst 5%, from this po's own tax line", self.expected), [])


if __name__ == "__main__":
    unittest.main()
