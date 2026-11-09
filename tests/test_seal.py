"""Sam's yes, sealed, and the numbering of records. Found by the run 1 attack on a real house,
2026-11-09 (attack ids in each test name). Run from the repo root:

    python -m unittest discover -s tests -v
"""
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "03 compare"))
import compare  # noqa: E402
import grid_check  # noqa: E402  (compare puts 02 read on the path)
import grid_rules as rules  # noqa: E402
import seal  # noqa: E402
from chain import chain_problems  # noqa: E402
from sealing import resealed  # noqa: E402
from test_money_gate import money, texts  # noqa: E402

HOUSE = "77-mockup-drive"
RB = ROOT / "02 read" / HOUSE / "read-back-1.md"


def gate_problems(**records):
    return money.expected_request(dict(texts(), **records))[1]


class SamsYes(unittest.TestCase):
    def test_a20_not_yet_is_not_a_yes(self):
        review = texts()["review"]
        planted = re.sub(r"^-\s*Answer:.*$", "- Answer: Not yet. Sam will say yes once he has checked the lockers.",
                         review, count=1, flags=re.M)
        problems = gate_problems(review=resealed("review-1.md", planted, check=False))
        self.assertTrue(any("not a plain yes" in p for p in problems), problems)

    def test_seal_refuses_an_answer_that_is_not_yes(self):
        draft = "---\nstatus: draft\n---\n## Sam's yes\n- Answer: I don't know\n- Name: Sam\n- Date: 2026-11-09\n"
        with self.assertRaises(ValueError):
            seal.seal_text("review-1.md", draft)

    def test_seal_refuses_a_yes_with_no_name_or_date(self):
        with self.assertRaises(ValueError):
            seal.seal_text("review-1.md", "---\nstatus: draft\n---\n- Answer: yes\n- Name:\n- Date:\n")

    def test_sealed_yes_is_approved(self):
        draft = "---\nstatus: draft\n---\n- Answer: yes, to the whole table\n- Name: Sam\n- Date: 2026-11-09\n"
        sealed = seal.seal_text("review-1.md", draft)
        self.assertEqual(seal.approval_problems(sealed, "review-1.md"), [])
        self.assertTrue(money.approved(sealed))

    def test_approved_by_hand_without_a_seal_is_refused(self):
        unsealed = seal.unsealed(texts()["review"])
        self.assertIn("approved", unsealed)
        problems = gate_problems(review=unsealed)
        self.assertTrue(any("has no seal" in p for p in problems), problems)


class EditsAfterTheYes(unittest.TestCase):
    def test_a05_flipped_decision_in_approved_review_is_refused(self):
        review = texts()["review"]
        planted = review.replace("| off (not chosen) |", "| on (Sam: chase the stringers) |", 1)
        self.assertNotEqual(planted, review)
        problems = gate_problems(review=planted)
        self.assertTrue(any("changed after Sam's yes" in p for p in problems), problems)

    def test_a02_edited_approved_read_back_is_refused_with_the_seal_message(self):
        text = RB.read_text(encoding="utf-8")
        planted = text.replace("| 34 ", "| 44 ", 1) if "| 34 " in text else text.replace("34 ft", "44 ft", 1)
        self.assertNotEqual(planted, text)
        self.assertIn(seal.CHANGED, seal.approval_problems(planted, RB.name))
        grid = (RB.with_name("grid-1.md")).read_text(encoding="utf-8")
        snapshot = RB.with_name("price-list-1.csv").read_bytes()
        problems, _ = grid_check.check_grid(planted, grid, snapshot, final=True)
        self.assertFalse(any("Rebuild the grid" in p for p in problems), problems)
        self.assertTrue(any("changed after Sam's yes" in p for p in problems), problems)

    def test_a21_approved_read_back_copied_under_a_new_number_is_refused(self):
        problems = seal.approval_problems(RB.read_text(encoding="utf-8"), "read-back-2.md")
        self.assertTrue(any("copied under a new name" in p for p in problems), problems)


class Numbering(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "02 read" / "h").mkdir(parents=True)

    def record(self, name, attempt, origin):
        path = self.tmp / "02 read" / "h" / name
        path.write_text(f"---\nattempt: {attempt}\nfrom: {origin}\n---\n", encoding="utf-8")
        return path

    def test_a27_attempt_that_disagrees_with_the_file_name_is_refused(self):
        path = self.record("review-1.md", 2, "02 read")
        self.assertTrue(any("attempt: 2" in p for p in chain_problems(path, path.read_text(), self.tmp)))

    def test_a25_a_gap_below_is_refused(self):
        path = self.record("read-back-3.md", 3, "02 read")
        self.record("read-back-1.md", 1, "02 read")
        problems = chain_problems(path, path.read_text(), self.tmp)
        self.assertTrue(any("read-back-2.md is missing" in p for p in problems), problems)

    def test_o7_a_from_line_in_prose_is_refused(self):
        path = self.record("read-back-1.md", 1, "02 read/h/ and Sam's answers (2026-11-09)")
        self.assertTrue(any("from: must name exactly one" in p for p in chain_problems(path, path.read_text(), self.tmp)))

    def test_a_clean_record_passes(self):
        path = self.record("read-back-1.md", 1, "`02 read/h/`")
        self.assertEqual(chain_problems(path, path.read_text(), self.tmp), [])

    def test_the_worked_example_is_clean(self):
        for path in (RB, ROOT / "03 compare" / HOUSE / "variance-1.md", ROOT / "04 review" / HOUSE / "review-1.md"):
            self.assertEqual(chain_problems(path, path.read_text(encoding="utf-8"), ROOT), [], path.name)


class Compare(unittest.TestCase):
    def test_a10_a_second_variance_from_the_same_read_back_is_refused(self):
        folder = ROOT / "03 compare" / HOUSE
        message = compare.already_compared(folder, HOUSE, "read-back-1.md")
        self.assertIn("variance-1.md already comes from read-back-1.md", message or "")
        self.assertIsNone(compare.already_compared(folder, HOUSE, "read-back-2.md"))

    def test_compare_refuses_an_edited_approved_read_back(self):
        planted = RB.read_text(encoding="utf-8").replace("Sam", "Sam ", 1)
        self.assertFalse(compare.calc.sams_yes(planted))


class CountMayAskSam(unittest.TestCase):
    def test_a23_count_can_be_answered_ask_sam_and_final_refuses_it(self):
        allowed = rules.ROW_RULES["count"][2]
        self.assertIsNone(grid_check.answer_problem("ask Sam: is 9' a length or a height?", allowed))


if __name__ == "__main__":
    unittest.main()
