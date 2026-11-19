"""The phone app's runner, step 4: compare by code, the Difference screen's rows and defaults, and
Sam's picks written into review-N.md and sealed (seal.py runs the request's money gate first).
Runs on 77 Mockup Drive taken back to its sealed read-back."""
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import difference  # noqa: E402
import houses  # noqa: E402
import steps  # noqa: E402
from folder import Folder  # noqa: E402

HOUSE = "77-mockup-drive"
LEAVE_OUT = shutil.ignore_patterns(".git", ".venv", "tests", "docs", "_for-testers", "__pycache__", "real-*", "app")
DAY = date(2026, 11, 14)
OWN_GROUP = {"7": {"on": True, "epo": ""}}


class Difference(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT, self.tmp / "f", ignore=LEAVE_OUT)
        self.folder = Folder(self.tmp / "f")
        for stage in ("03 compare", "04 review", "05 request"):
            shutil.rmtree(self.folder.stage(stage, HOUSE))
        steps.run_compare(self.folder, HOUSE)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def screen(self):
        return houses.stand(self.folder, HOUSE)["screen"]

    def review(self):
        return (self.folder.stage("04 review", HOUSE) / "review-1.md").read_text(encoding="utf-8")

    def test_compare_runs_once_then_the_difference_shows(self):
        self.assertEqual(self.screen(), houses.DIFFERENCE)
        with self.assertRaises(steps.Stopped):
            steps.run_compare(self.folder, HOUSE)

    def test_only_rows_that_differ_with_their_defaults(self):
        rows = {r["row"]: r for r in difference.screen(self.folder, HOUSE)["rows"]}
        self.assertEqual(sorted(rows), ["3", "5", "7"])
        self.assertEqual((rows["3"]["default"], rows["5"]["default"]), ("on", "off"))
        self.assertTrue(rows["7"]["no_po"] and rows["7"]["epo_asks"])
        self.assertIsNone(rows["7"]["default"])  # flagged, on no PO, no standing answer: his call

    def test_picks_are_written_and_sealed(self):
        steps.review_yes(self.folder, HOUSE, OWN_GROUP, today=DAY)
        text = self.review()
        self.assertIn("status: approved", text)
        self.assertIn("| 3 | MKR-02402401/027 | 8' doors and trim | +$300.00 | flag | on |", text)
        self.assertIn("| 5 | MKR-02402401/027 | Stringer, inside or outside | +$36.00 | ignore | off (Sam did not choose it) |", text)
        self.assertEqual(self.screen(), houses.PDF)

    def test_no_po_row_needs_its_epo_answered(self):
        with self.assertRaises(steps.Stopped) as caught:
            steps.review_yes(self.folder, HOUSE, {}, today=DAY)
        self.assertIn("needs your call", str(caught.exception))
        with self.assertRaises(steps.Stopped) as caught:
            steps.review_yes(self.folder, HOUSE, {"7": {"on": True}}, today=DAY)
        self.assertIn("on no PO", str(caught.exception))
        self.assertFalse((self.folder.stage("04 review", HOUSE) / "review-1.md").exists())

    def test_flagged_row_off_needs_his_reason(self):
        picks = {**OWN_GROUP, "3": {"on": False}}
        with self.assertRaises(steps.Stopped):
            steps.review_yes(self.folder, HOUSE, picks, today=DAY)
        steps.review_yes(self.folder, HOUSE, {**OWN_GROUP, "3": {"on": False, "reason": "doors were ours"}}, today=DAY)
        self.assertIn("off (Sam: doors were ours)", self.review())

    def test_all_off_is_nothing_to_ask_for(self):
        picks = {"3": {"on": False, "reason": "doors were ours"}, "7": {"on": False}}
        with self.assertRaises(steps.Stopped):
            steps.review_yes(self.folder, HOUSE, picks, today=DAY)
        steps.review_yes(self.folder, HOUSE, picks, today=DAY, none_reason="builder already paid this house")
        self.assertEqual(self.screen(), houses.NO_REQUEST)
        text = self.review()
        self.assertIn("| 3 | MKR-02402401/027 | 8' doors and trim | +$300.00 | flag | off (Sam: doors were ours) |", text)
        self.assertIn("ignore | off (Sam: builder already paid this house) |", text)
        self.assertNotIn("did not choose", text)

    def test_refused_review_is_taken_back_out(self):
        with self.assertRaises(steps.Stopped) as caught:
            steps.review_yes(self.folder, HOUSE, OWN_GROUP, today=date(2099, 1, 1))
        self.assertIn("Stopped before the money", str(caught.exception))
        self.assertFalse((self.folder.stage("04 review", HOUSE) / "review-1.md").exists())
        self.assertEqual(self.screen(), houses.DIFFERENCE)

    def test_stale_row_is_refused(self):
        with self.assertRaises(steps.Stopped):
            steps.review_yes(self.folder, HOUSE, {**OWN_GROUP, "99": {"on": True}}, today=DAY)


if __name__ == "__main__":
    unittest.main()
