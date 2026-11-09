"""Loop run 3 on a real house, 2026-11-09: the request-stage breaks the attacker found. Run from the
repo root: python -m unittest discover -s tests -v

a44: a request marked sent could be asked for again through a second review.
a42: the job line could swap the house number and the lot (the sorted digits still agreed).
a38: with a standing answer for work on no PO, a blank "EPO goes on" passed.
advice: one missing snapshot printed 15 lines and advice to write a new read-back.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import header_checks  # noqa: E402
import house_checks  # noqa: E402

HEAD = ("| Row | PO number | Item | Variance | Call | Sam's decision (on / off) | Reason, if a flagged row is "
        "taken off | EPO goes on |\n|---|---|---|---|---|---|---|---|\n")


def review(*rows):
    return "# h, review 1\n\n" + HEAD + "".join(rows)


def row(num, po, item, decision, reason="", epo=""):
    return f"| {num} | {po} | {item} | +$100.00 | flag | {decision} | {reason} | {epo} |\n"


class Folder(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)

    def write(self, rel, text):
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class SentRowsAreNotAskedAgain(Folder):
    FIRST = review(row("7", "AB-1/027", "Locker detail", "on"), row("6", "AB-1/027", "8' doors and trim", "off"))

    def check(self, sent, now):
        self.write("04 review/h/review-1.md", self.FIRST)
        self.write("05 request/h/request-check-1.md",
                   f"from review: 04 review/h/review-1.md\n\n## Sam's yes to send\n- Answer: yes\n- sent: {sent}\n")
        return house_checks.sent_problems(self.dir, self.dir / "05 request" / "h", now)

    def test_a_sent_row_on_a_new_review_is_refused(self):
        problems = self.check("yes", review(row("7", "AB-1/027", "Locker detail", "on")))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("vpo-request-1.pdf", problems[0])
        self.assertIn("06 outcome", problems[0])

    def test_an_unsent_request_does_not_block(self):
        self.assertEqual(self.check("no (practice run)", review(row("7", "AB-1/027", "Locker detail", "on"))), [])

    def test_a_row_left_off_before_can_go_on_now(self):
        self.assertEqual(self.check("yes", review(row("6", "AB-1/027", "8' doors and trim", "on"))), [])


class JobLineIsExact(unittest.TestCase):
    HEADER = {"address": "40 Sample Crescent", "lot": ["22", "6"]}

    def test_the_right_job_line_passes(self):
        self.assertEqual(header_checks.job_text_problems("40 Sample Crescent, lot 22, block 6", self.HEADER), [])

    def test_house_number_and_lot_swapped_is_refused(self):
        problems = header_checks.job_text_problems("22 Sample Crescent, lot 40, block 6", self.HEADER)
        self.assertEqual(len(problems), 2, problems)

    def test_a_different_street_with_the_same_digits_is_refused(self):
        problems = header_checks.job_text_problems("40 Sample Drive, lot 22, block 6", self.HEADER)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("word for word", problems[0])

    def test_lot_and_block_in_the_wrong_order_is_refused(self):
        problems = header_checks.job_text_problems("40 Sample Crescent, lot 6, block 22", self.HEADER)
        self.assertEqual(len(problems), 1, problems)


class StandingAnswerForWorkOnNoPO(unittest.TestCase):
    SETUP = "| Work on no PO goes on | Sample Builder Ltd.: the main PO. |\n"

    def test_blank_target_is_refused(self):
        problems = house_checks.standing_epo_problems(review(row("13", "none", "Mantle", "on")), self.SETUP)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("standing answer", problems[0])

    def test_filled_target_passes(self):
        text = review(row("13", "none", "Mantle", "on", epo="AB-1/027"))
        self.assertEqual(house_checks.standing_epo_problems(text, self.SETUP), [])

    def test_sams_own_answer_in_the_reason_passes(self):
        text = review(row("13", "none", "Mantle", "on", reason="Sam: keep it in its own group"))
        self.assertEqual(house_checks.standing_epo_problems(text, self.SETUP), [])

    def test_ask_each_time_does_not_enforce(self):
        setup = "| Work on no PO goes on | Ask each time. (Stand-in.) |\n"
        self.assertEqual(house_checks.standing_epo_problems(review(row("13", "none", "Mantle", "on")), setup), [])


class OneFixForTheProblem(Folder):
    def test_missing_snapshot_shows_only_its_own_line(self):
        snap = "the snapshot price-list-1.csv named in the read-back is not in the house's 02 read folder"
        rows = [f"row {n}, price: fail: 'x' is not on the price list snapshot. Stop and ask Sam" for n in range(7)]
        shown, advice = house_checks.stop_message(self.dir, "h", [snap] + rows + [snap])
        self.assertEqual(shown, [snap])
        self.assertIn("put the original price list snapshot back", advice)

    def test_hand_edited_variance_says_run_compare(self):
        problem = "variance row 'mantle' (none): measured qty 10 is not Sam's size as read back (9)"
        shown, advice = house_checks.stop_message(self.dir, "h", [problem, problem])
        self.assertEqual(shown, [problem])
        self.assertIn("never edit a variance", advice)
        self.assertIn("compare.py", advice)


if __name__ == "__main__":
    unittest.main()
