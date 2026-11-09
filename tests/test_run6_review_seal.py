"""Loop run 6, 2026-11-09 (a real house). Run from the repo root:

    python -m unittest discover -s tests

1. seal.py sealed reviews the request build would always refuse ("on hold", an item written with a
   hyphen, a from: naming a read-back), so a review number was used up; and a Date of 2026-11-31
   passed the seal and crashed the build with a traceback.
2. A hand-edited "Total variance" line passed while every row was right.
3. A row printed with the wrong unit (a railing in SF) was numbered.
4. A row already on a sent request in another house folder could be asked for again.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import header_checks  # noqa: E402
import house_checks  # noqa: E402
import review_gate  # noqa: E402
import row_checks  # noqa: E402
import variance_words  # noqa: E402

HOUSE = "77-mockup-drive"
LEAVE_OUT = shutil.ignore_patterns(".git", "tests", "__pycache__", "_for-testers")


class ReviewSealRunsTheBuildChecks(unittest.TestCase):
    """seal.py on a review-2 of the sample house, in a throwaway copy of the folder."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.copy = cls.tmp / "folder"
        shutil.copytree(ROOT, cls.copy, ignore=LEAVE_OUT)
        text = (ROOT / "04 review" / HOUSE / "review-1.md").read_text(encoding="utf-8")
        text = re.sub(r"^sealed:.*\n", "", text, flags=re.M)
        text = text.replace("status: approved", "status: draft").replace("attempt: 1", "attempt: 2")
        cls.clean = text

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def seal(self, text):
        path = self.copy / "04 review" / HOUSE / "review-2.md"
        path.write_text(text, encoding="utf-8", newline="\n")
        try:
            done = subprocess.run([sys.executable, "02 read/seal.py", str(path)], cwd=self.copy,
                                  capture_output=True, text=True, encoding="utf-8")
            return done.returncode, done.stdout + done.stderr
        finally:
            path.unlink(missing_ok=True)
            book = path.parent / "seals.md"
            book.write_text("".join(l for l in book.read_text(encoding="utf-8").splitlines(True)
                                    if "review-2.md" not in l), encoding="utf-8", newline="\n")

    def refused(self, text, words):
        code, said = self.seal(text)
        self.assertNotEqual(code, 0, said)
        self.assertIn(words, said)
        self.assertNotIn("Traceback", said)

    def test_a_clean_review_still_seals(self):
        code, said = self.seal(self.clean)
        self.assertEqual(code, 0, said)

    def test_on_hold_is_refused_at_the_seal(self):
        self.refused(self.clean.replace("| on (flagged rows go on unless Sam takes one off) |",
                                        "| on hold (ask the super first) |", 1), "no on/off decision")

    def test_an_item_not_in_the_variance_is_refused_at_the_seal(self):
        self.refused(self.clean.replace("| 8' doors and trim |", "| 8' doors & trim |", 1), "not in the variance")

    def test_a_from_line_naming_a_read_back_is_refused(self):
        self.refused(self.clean.replace("from: 03 compare/77-mockup-drive/variance-1.md",
                                        "from: 02 read/77-mockup-drive/read-back-1.md"), "a review comes from")

    def test_a_day_that_does_not_exist_is_refused_without_a_traceback(self):
        self.refused(self.clean.replace("- Date: 2026-10-17", "- Date: 2026-11-31"), "not a real day")

    def test_a_date_after_today_is_refused(self):
        self.refused(self.clean.replace("- Date: 2026-10-17", "- Date: 2099-01-01"), "after today")


class DatesNeverCrash(unittest.TestCase):
    def test_review_gate_reads_a_bad_day_in_words(self):
        problems = review_gate.date_problems("- Date: 2026-02-30\n", today=date(2026, 11, 9))
        self.assertEqual(len(problems), 1, problems)

    def test_header_check_reads_a_bad_review_date_in_words(self):
        problems = header_checks.facts_problems("prepared november 9, 2026", {"review_date": "2026-11-31"})
        self.assertTrue(any("not a real day" in p for p in problems), problems)


class VarianceTotalsAreChecked(unittest.TestCase):
    FIGURES = {("a-1/065", "railing", "9"): {"po_amount": Decimal("600"), "measured_value": Decimal("640"),
                                             "difference": Decimal("40")}}

    def totals(self, variance):
        return variance_words.total_problems(variance, self.FIGURES)

    def test_totals_as_compare_wrote_them_pass(self):
        self.assertEqual(self.totals("- Total of POs: $600.00\n- Total measured value: $640.00\n"
                                     "- Total variance: +$40.00 ($640.00 - $600.00)\n"), [])

    def test_a_hand_edited_total_is_refused(self):
        problems = self.totals("- Total of POs: $600.00\n- Total measured value: $640.00\n"
                               "- Total variance: +$3,550.00 ($640.00 - $600.00)\n")
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("Total variance", problems[0])


class UnitIsChecked(unittest.TestCase):
    ROW = {"item": "railing, wood", "po": "A-1/065", "unit": "LF"}

    def test_the_right_unit_passes(self):
        self.assertEqual(row_checks.unit_problems(self.ROW, " lf $40.00 15 $40.00 $600.00 16 $640.00 +$40.00"), [])

    def test_a_wrong_unit_is_refused(self):
        self.assertEqual(len(row_checks.unit_problems(self.ROW, " sf $40.00 15 $40.00 $600.00 16 $640.00 +$40.00")), 1)

    def test_a_two_word_unit_passes(self):
        row = dict(self.ROW, unit="Floor SF")
        self.assertEqual(row_checks.unit_problems(row, " floor sf $2.90 1488 $2.90 $4,315.20 1488"), [])


class SentInAnotherHouse(unittest.TestCase):
    REVIEW = ("| Row | PO number | Item | Variance | Call | Sam's decision (on / off) | Reason | EPO goes on |\n"
              "|---|---|---|---|---|---|---|---|\n| 9 | A-1/065 | Railing | +$40.00 | ignore | on | | |\n")

    def test_a_row_sent_from_another_house_folder_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "04 review" / "h").mkdir(parents=True)
            (root / "04 review" / "h" / "review-1.md").write_text(self.REVIEW, encoding="utf-8")
            (root / "05 request" / "h").mkdir(parents=True)
            (root / "05 request" / "h" / "request-check-1.md").write_text(
                "from review: 04 review/h/review-1.md\n\n- Answer: yes\n- sent: yes\n", encoding="utf-8")
            (root / "05 request" / "h-2").mkdir(parents=True)
            problems = house_checks.sent_problems(root, root / "05 request" / "h-2", self.REVIEW)
            self.assertEqual(len(problems), 1, problems)
            self.assertIn("in house h", problems[0])


if __name__ == "__main__":
    unittest.main()
