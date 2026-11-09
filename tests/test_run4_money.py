"""Loop run 4 on a real house, 2026-11-09: the money gate and the request. Run from the repo root:

    python -m unittest discover -s tests -v

1. A PO that prints its tax but no percentage had its rate taken as tax / subtotal: 225.69 on
   4513.70 is 5.00011%, so a correct request printing "PST 5%" was refused, and a no-PO row was
   refused for "different tax rates" when every PO charges 5%.
2. Work on no PO went on the touch-up PO though the standing answer says the main PO.
3. A request with no row on was numbered.
4. The variance's Why and Call could be edited by hand after the review.
5. The template line "- sent: yes / no" was read as sent.
"""
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import house_checks  # noqa: E402
import taxes  # noqa: E402
import variance_words  # noqa: E402


class TaxFromRoundedAmount(unittest.TestCase):
    def test_rounded_tax_gives_the_plain_rate(self):
        self.assertEqual(taxes.printed_rates(Decimal("4513.70"), "GST/HST $0.00; PST $225.69"), (Decimal("0.05"),))

    def test_exact_tax_still_reads(self):
        self.assertEqual(taxes.printed_rates(Decimal("1000.00"), "GST/HST $0.00; PST $50.00"), (Decimal("0.05"),))

    def test_two_pos_at_five_percent_share_one_rate(self):
        rates = {"A-1/065": taxes.printed_rates(Decimal("4513.70"), "PST $225.69"),
                 "A-1/066": taxes.printed_rates(Decimal("500.00"), "PST $25.00")}
        found = []
        self.assertEqual(taxes.group_rate("none", rates, found), (Decimal("0.05"),))
        self.assertEqual(found, [])


SETUP = "| Work on no PO goes on | Sample Builder: the main PO, the one with the whole list of work. |\n"
READ_BACK = """## Rows
| # | PO number | Line as printed | Unit price | Price list item |
|---|---|---|---|---|
| 1 | A-1/065 | Paint | $2.90 | Basic painting |
| 2 | A-1/065 | Doors | $125.00 | Exterior door |
| 3 | A-1/065 | Offset | $-1500.00 | not on the price list |
| 4 | A-1/066 | Touch up | $500.00 | not on the price list |
| 5 | none | (on no PO) | | Stubwall |
"""
REVIEW = """| Row | PO number | Item | Variance | Call | Sam's decision (on / off) | Reason, if a flagged row is taken off | EPO goes on |
|---|---|---|---|---|---|---|---|
| 5 | none | Stubwall | +$36.00 | ignore | on | {reason} | {target} |
"""


class MainPOForWorkOnNoPO(unittest.TestCase):
    def check(self, target, reason=""):
        return house_checks.standing_epo_problems(REVIEW.format(target=target, reason=reason), SETUP, READ_BACK)

    def test_the_main_po_passes(self):
        self.assertEqual(self.check("A-1/065"), [])

    def test_another_po_is_refused_naming_the_main_one(self):
        problems = self.check("A-1/066")
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("A-1/065", problems[0])

    def test_sams_own_answer_overrides(self):
        self.assertEqual(self.check("A-1/066", "Sam: put it on the touch-up PO"), [])

    def test_blank_is_still_refused(self):
        self.assertEqual(len(self.check("")), 1)


class SentMeansSentYes(unittest.TestCase):
    def house(self, sent_line):
        d = tempfile.TemporaryDirectory()
        root = Path(d.name)
        (root / "04 review" / "h").mkdir(parents=True)
        (root / "05 request" / "h").mkdir(parents=True)
        (root / "04 review" / "h" / "review-1.md").write_text(REVIEW.format(target="A-1/065", reason=""),
                                                              encoding="utf-8")
        (root / "05 request" / "h" / "request-check-1.md").write_text(
            f"from review: 04 review/h/review-1.md\n\n## Sam's yes to send\n- Answer:\n{sent_line}\n",
            encoding="utf-8")
        self.addCleanup(d.cleanup)
        return root

    def problems(self, sent_line):
        root = self.house(sent_line)
        return house_checks.sent_problems(root, root / "05 request" / "h", REVIEW.format(target="A-1/065", reason=""))

    def test_the_blank_template_line_is_not_sent(self):
        self.assertEqual(self.problems("- sent: yes / no"), [])
        self.assertEqual(self.problems("- sent:"), [])

    def test_sent_yes_still_blocks(self):
        self.assertEqual(len(self.problems("- sent: yes")), 1)


VARIANCE = """## Rows
| Row | PO number | Item | Unit | Agreed rate | PO qty | PO rate | PO amount | Measured qty | Measured value | Variance | Why | Call |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | A-1/065 | Railing | LF | $40.00 | 15 | $40.00 | $600.00 | 16 | $640.00 | +$40.00 | {why} | {call} |

## Totals, before tax
- House flagged on total: {flag} ($40.00 against the flag line $100.00)
"""
LIMITS = "| Ignore line | under $50 |\n| Flag line | $100 and up. |\n"
FIGURES = {("A-1/065", "railing", "8"): {"po_qty": Decimal(15), "po_rate": Decimal(40), "rate": Decimal(40),
                                        "po_amount": Decimal(600), "measured_qty": Decimal(16),
                                        "difference": Decimal(40)}}


class VarianceWordsAreCode(unittest.TestCase):
    def check(self, why="PO quantity short", call="ignore", flag="no"):
        return variance_words.problems(VARIANCE.format(why=why, call=call, flag=flag), FIGURES, LIMITS)

    def test_as_compare_wrote_it_passes(self):
        self.assertEqual(self.check(), [])

    def test_a_call_changed_by_hand_is_refused(self):
        self.assertEqual(len(self.check(call="flag")), 1)

    def test_a_why_changed_by_hand_is_refused(self):
        self.assertEqual(len(self.check(why="PO rate differs from the agreed rate")), 1)

    def test_an_old_variance_without_row_numbers_is_matched_by_po_and_item(self):
        old = VARIANCE.replace("| Row | PO number", "| PO number").replace("| 8 | A-1/065", "| A-1/065")
        self.assertEqual(len(variance_words.problems(old.format(why="PO quantity short", call="flag", flag="no"),
                                                     FIGURES, LIMITS)), 1)

    def test_the_house_flag_changed_by_hand_is_refused(self):
        self.assertEqual(len(self.check(flag="yes")), 1)


if __name__ == "__main__":
    unittest.main()
