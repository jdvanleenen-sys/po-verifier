"""The variance written by code, checked by the money gate it was kept apart from. Run from the root:

    python -m unittest discover -s tests -v

Uses only 77 Mockup Drive. compare.py and money.py work the numbers out separately; every case
here must come out the same in both.
"""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "03 compare"))
import compare  # noqa: E402
import compare_rows as calc  # noqa: E402
from test_money_gate import money, texts  # noqa: E402

HOUSE = "77-mockup-drive"
LIMITS = (Decimal(50), Decimal(100), "approved, practice stand-ins")
EPO_HEADER = ("| EPO name | Created by | PO it is against | Item it pays for | Total | Reason code | Account code "
              "| Notes | Trade partner | Date requested | Which way the money goes | Status |\n|" + "---|" * 12)


def variance_for(records):
    path = ROOT / "02 read" / HOUSE / "read-back-1.md"
    compared, aside, problems = calc.work_out(records["read-back"], records["grid"])
    return compare.render(HOUSE, 2, path, records["read-back"], compared, aside, LIMITS), compared, problems


def with_epo(row, po, total, which_way):
    epo = (f"| V00999-{po}-E01 | Site super | {po} | row {row} | {total} | EXTRA | PAIN | practice "
           f"| Sample Painting Co. | 10/10/2026 | {which_way} | Approved |")
    return texts(**{"read-back": ("\nnone in the folder\n", f"\n{EPO_HEADER}\n{epo}\n")})


def gate(records, variance_text):
    records = dict(records, variance=variance_text)
    return money.expected_request(records)


def row(compared, num):
    return next(r for r in compared if r["num"] == num)


class SameAsTheGate(unittest.TestCase):
    def test_77_comes_out_as_the_hand_checked_variance(self):
        text, compared, problems = variance_for(texts())
        self.assertEqual(problems, [])
        self.assertEqual(sum(r["variance"] for r in compared), Decimal("1008.00"))
        exp, found = gate(texts(), text)
        self.assertEqual(found, [])
        self.assertEqual(exp["house"]["total"], Decimal("1020.60"))

    def test_epo_that_pays_sam_counts_in_the_po_amount(self):
        records = with_epo(3, "MKR-02402401/027", "$120.00", "pays Sam")
        text, compared, problems = variance_for(records)
        self.assertEqual((problems, row(compared, "3")["variance"]), ([], Decimal("180.00")))
        self.assertIn("EPO +$120.00 counted in the PO amount", text)
        self.assertNotIn("the read-back gives", " ".join(gate(records, text)[1]))

    def test_back_charge_against_sam_takes_away(self):
        records = with_epo(6, "MKR-02402401/041", "$150.00", "back charge against Sam")
        text, compared, problems = variance_for(records)
        self.assertEqual((problems, row(compared, "6")["variance"]), ([], Decimal("150.00")))
        self.assertNotIn("the read-back gives", " ".join(gate(records, text)[1]))

    def test_back_charge_against_another_trade_pays_sam_in_both(self):
        records = with_epo(3, "MKR-02402401/027", "$120.00", "pays Sam: back charge against another trade")
        text, compared, problems = variance_for(records)
        self.assertEqual((problems, row(compared, "3")["variance"]), ([], Decimal("180.00")))
        self.assertNotIn("the read-back gives", " ".join(gate(records, text)[1]))

    def test_not_comparable_row_is_set_apart_and_the_gate_agrees(self):
        records = texts(grid=("pass: 34 LF against PO qty 30", "not comparable: stringers are a lump sum here"))
        text, compared, problems = variance_for(records)
        self.assertEqual(problems, [])
        self.assertNotIn("5", [r["num"] for r in compared])
        self.assertIn("row 5: Stringer, inside or outside | not comparable: stringers are a lump sum here", text)
        found = [p for p in gate(records, text)[1] if not p.startswith("review row")]
        self.assertFalse(any("stringer" in p.lower() for p in found), found)


class Refused(unittest.TestCase):
    def test_epo_that_names_no_row(self):
        records = with_epo(3, "MKR-02402401/027", "$120.00", "pays Sam")
        records["read-back"] = records["read-back"].replace("| row 3 |", "| the doors |")
        self.assertTrue(any("no 'row N'" in p for p in variance_for(records)[2]))

    def test_epo_against_another_po(self):
        records = with_epo(3, "MKR-02402401/041", "$120.00", "pays Sam")
        self.assertTrue(any("different PO" in p for p in variance_for(records)[2]))

    def test_read_back_without_sams_yes(self):
        self.assertFalse(calc.sams_yes(texts()["read-back"].replace("status: approved", "status: draft")))
        self.assertTrue(calc.sams_yes(texts()["read-back"]))


class Calls(unittest.TestCase):
    def test_threshold_edges(self):
        ignore, flag, _ = LIMITS
        cases = {"0": "matches", "49.99": "ignore", "-49.99": "ignore", "50": "Sam's call",
                 "99.99": "Sam's call", "100": "flag", "-100": "flag"}
        for value, want in cases.items():
            self.assertEqual(calc.call(Decimal(value), ignore, flag), want, value)

    def test_rate_that_differs_is_named(self):
        r = {"po": "X/1", "measured_qty": Decimal(5), "po_qty": Decimal(5), "po_rate": Decimal(9),
             "rate": Decimal(10), "epo": Decimal(0)}
        self.assertEqual(calc.why(r), "PO rate differs from the agreed rate")

    def test_back_charge_against_another_trade_still_pays_sam(self):
        self.assertEqual(calc.epo_sign("back charge against another trade; pays Sam"), 1)
        self.assertEqual(calc.epo_sign("It's a back charge against me."), -1)

    def test_thresholds_read_from_the_contractor_file(self):
        ignore, flag, note = calc.thresholds(calc.CONTRACTOR.read_text(encoding="utf-8"))
        self.assertEqual((ignore, flag), (Decimal(50), Decimal(100)))
        self.assertIn("practice stand-ins", note)


if __name__ == "__main__":
    unittest.main()
