"""The PDF checks read the labelled line, with its sign. Run from the repo root:

    python -m unittest discover -s tests -v

Planted on request text laid out the way the real PDF reads (see 05 request/77-mockup-drive):
a credit printed as money owed, a right number in the wrong box, a group total on the wrong PO.
Each must fail. The clean versions must pass. No browser needed.
"""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import verify  # noqa: E402

PO = "MKR-02402431/027"
CREDIT_PO = "MKR-02402431/033"


def request_text(before, tax, total, groups):
    """Request text in the order the real PDF prints it: three boxes, then one block per group."""
    head = ("VPO request\nDOCUMENT\nVR-0001, page 1 of 1\nBEFORE TAX\n" + before + "\n2 items\nTAX\n" + tax +
            "\nGST/HST 5%, at the rate printed on each PO.\nTOTAL REQUESTED\n" + total +
            "\nPO " + PO + ": $X. Credits included.\n")
    body = ""
    for heading, diff, gst, ask in groups:
        body += (heading + "\nITEM\nUNIT\nsome row\n" + diff + "\nDifference before tax\n" + diff +
                 "\nGST/HST 5%, from this PO's own tax line\n" + gst + "\n" + ask + "\n")
    return head + body + "Checked and approved by (trade contractor)\n"


def expected(groups):
    out = {"groups": {}, "house": {"before": D(0), "tax": D(0), "total": D(0)}}
    for po, before, tax in groups:
        out["groups"][po] = {"before": D(before), "tax": D(tax), "total": D(before) + D(tax)}
        out["house"]["before"] += D(before)
        out["house"]["tax"] += D(tax)
    out["house"]["total"] = out["house"]["before"] + out["house"]["tax"]
    return out


MIXED = expected([(PO, "532.00", "26.60"), (CREDIT_PO, "-720.00", "-36.00"), ("none", "300.00", "15.00")])
MIXED_GROUPS = [
    ("PO " + PO + " Interior paint and stain. One EPO for this PO.", "+$532.00", "$26.60", "EPO requested for this PO\n$558.60"),
    ("PO " + CREDIT_PO + " Doors. A credit back to the builder.", "-$720.00", "-$36.00", "Credit back to the builder for this PO\n-$756.00"),
    ("No PO Work done on site that is on no PO.", "+$300.00", "$15.00", "New PO or EPO requested\n$315.00"),
]


def passes(result):
    return ": pass:" in result


class SignedHouseTotals(unittest.TestCase):
    def test_clean_mixed_house_passes(self):
        text = request_text("$112.00", "$5.60", "$117.60", MIXED_GROUPS)
        self.assertTrue(passes(verify.check_house(text, MIXED)), verify.check_house(text, MIXED))

    def test_credit_house_printed_as_owed_fails(self):
        credit = expected([(CREDIT_PO, "-720.00", "-36.00")])
        groups = [MIXED_GROUPS[1]]
        clean = request_text("-$720.00", "-$36.00", "-$756.00", groups)
        self.assertTrue(passes(verify.check_house(clean, credit)), verify.check_house(clean, credit))
        flipped = request_text("$720.00", "$36.00", "$756.00", groups)
        self.assertFalse(passes(verify.check_house(flipped, credit)))

    def test_right_number_in_the_wrong_box_fails(self):
        # 117.60 is printed (in a group line) but the Total requested box says 112.00.
        groups = MIXED_GROUPS[:2] + [("No PO Work done on site that is on no PO.", "+$300.00", "$15.00",
                                      "New PO or EPO requested\n$117.60")]
        text = request_text("$112.00", "$5.60", "$112.00", groups)
        self.assertFalse(passes(verify.check_house(text, MIXED)))


class SignedGroupTax(unittest.TestCase):
    def test_clean_mixed_groups_pass(self):
        text = request_text("$112.00", "$5.60", "$117.60", MIXED_GROUPS)
        self.assertTrue(passes(verify.check_tax(text, MIXED)), verify.check_tax(text, MIXED))

    def test_credit_group_printed_as_owed_fails(self):
        groups = list(MIXED_GROUPS)
        groups[1] = ("PO " + CREDIT_PO + " Doors.", "-$720.00", "$36.00", "EPO requested for this PO\n$756.00")
        text = request_text("$112.00", "$5.60", "$117.60", groups)
        self.assertFalse(passes(verify.check_tax(text, MIXED)))

    def test_totals_swapped_between_pos_fail(self):
        groups = [
            ("PO " + PO + " Interior paint.", "+$532.00", "$15.00", "EPO requested for this PO\n$315.00"),
            MIXED_GROUPS[1],
            ("No PO Work done on site that is on no PO.", "+$300.00", "$26.60", "New PO or EPO requested\n$558.60"),
        ]
        text = request_text("$112.00", "$5.60", "$117.60", groups)
        self.assertFalse(passes(verify.check_tax(text, MIXED)))

    def test_a_group_ending_in_made_up_words_fails(self):
        groups = list(MIXED_GROUPS)
        groups[1] = ("PO " + CREDIT_PO + " Doors.", "-$720.00", "-$36.00", "Refund owed for this PO\n-$756.00")
        text = request_text("$112.00", "$5.60", "$117.60", groups)
        self.assertFalse(passes(verify.check_tax(text, MIXED)))

    def test_a_missing_group_fails(self):
        text = request_text("$112.00", "$5.60", "$117.60", MIXED_GROUPS[:2])
        self.assertFalse(passes(verify.check_tax(text, MIXED)))


if __name__ == "__main__":
    unittest.main()
