"""Loop run 5, 2026-11-09 (a real house): a blank Answer was reported as "not a plain yes: ''", and
the grid asked the AI to match a note on rows that have none (done as ordered by a standing answer).
Run from the repo root: python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import grid_rules  # noqa: E402
import seal  # noqa: E402


class BlankAnswer(unittest.TestCase):
    def test_blank_answer_says_to_write_the_yes(self):
        text = "status: draft\n## Sam's yes\n- Answer:\n- Name: Sam\n- Date: 2026-11-09\n"
        problems = seal.yes_problems(text)
        self.assertTrue(any("no Answer yet" in p for p in problems), problems)


class DoneAsOrderedHasNoNote(unittest.TestCase):
    def test_note_match_is_code_filled(self):
        row = {"#": "2", "po number": "A-1/065", "po qty": "13", "unit price": "6.00", "line total": "78.00",
               "price list item": "Stringer, inside or outside",
               "sam measured (his words)": '"done as ordered"; 13; standing answer, contractor.md'}
        self.assertTrue(grid_rules.note_match(row, {}).startswith("n/a"))

    def test_a_real_note_still_goes_to_the_ai(self):
        row = {"#": "3", "po number": "A-1/065", "po qty": "15", "unit price": "8.00", "line total": "120.00",
               "price list item": "Handrail", "sam measured (his words)": "\"Handrail 14'\"; 14 ft"}
        self.assertEqual(grid_rules.note_match(row, {}), grid_rules.ASK)


if __name__ == "__main__":
    unittest.main()
