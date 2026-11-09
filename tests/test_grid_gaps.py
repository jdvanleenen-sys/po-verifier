"""Two gaps found on the first real house, 2026-11-08. Run from the repo root:

    python -m unittest discover -s tests -v

1. A "Sam measured" cell with none of his quoted words, such as "not in notes; see row 13", was read
   as a measurement of 13. Only a number after his quoted words is a measurement.
2. The final grid check passed a house whose "not on the price list" warnings had no answer from
   Sam, so compare would have left those lines unpriced without anyone deciding it.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import grid_check  # noqa: E402
import grid_rules as rules  # noqa: E402


def row(said):
    return {"#": "7", "po number": "A-1/094", "po qty": "6", "unit price": "40.00", "line total": "240.00",
            "price list item": "Handrail", "sam measured (his words)": said}


class NoQuoteNoMeasurement(unittest.TestCase):
    def test_pointer_to_another_row_is_not_a_measurement(self):
        self.assertIsNone(rules.measured_qty(row("not in notes; see row 13")))

    def test_unquoted_note_asks_sam(self):
        cell = rules.measured(row("not matched to a note; see row 13"), {})
        self.assertTrue(cell.startswith(rules.ASK_SAM), cell)

    def test_a_quoted_name_later_in_the_cell_is_not_the_measurement(self):
        said = "\"Handrail 14'\"; 14 ft; no colour given (photo, under \"24 Tillatson Downs\", line 2)"
        self.assertEqual(str(rules.measured_qty(row(said))), "14")

    def test_quoted_words_still_measure(self):
        self.assertEqual(str(rules.measured_qty(row('"Handrail 13\'"; 13 ft; no colour given'))), "13")


WARNING_ANSWERED = """
## WARNING: not on the price list (1 items)
| PO number | Description as printed | Qty and unit | Closest items | Sam's answer (add row / names item / leave unpriced) |
|---|---|---|---|---|
| A-1/093 | Wall Prime | 1 EA | none | {answer} |

## Rows
| # | PO number | Price list item |
|---|---|---|
| 1 | A-1/093 | not on the price list |
{extra}
"""


class WarningsNeedAnswers(unittest.TestCase):
    def check(self, answer, extra=""):
        return grid_check.warning_problems(WARNING_ANSWERED.format(answer=answer, extra=extra))

    def test_blank_answer_is_refused(self):
        problems = self.check("")
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("A-1/093", problems[0])

    def test_answered_warning_passes(self):
        self.assertEqual(self.check("leave unpriced: payment split"), [])

    def test_unpriced_row_missing_from_warning_table_is_refused(self):
        problems = self.check("leave unpriced", "| 2 | A-1/094 | not on the price list |")
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("2", problems[0])


if __name__ == "__main__":
    unittest.main()
