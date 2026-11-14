"""The phone app's runner: where a house stands, read off the folder's files. Each test runs on a
fresh copy of the folder with 77 Mockup Drive taken back to an earlier step."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import houses  # noqa: E402
from folder import Folder  # noqa: E402

HOUSE = "77-mockup-drive"
LEAVE_OUT = shutil.ignore_patterns(".git", ".venv", "tests", "docs", "_for-testers", "__pycache__", "real-*", "app")


class HouseState(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT, self.tmp / "f", ignore=LEAVE_OUT)
        self.folder = Folder(self.tmp / "f")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def drop(self, stage):
        shutil.rmtree(self.folder.stage(stage, HOUSE))

    def screen(self, **kw):
        return houses.stand(self.folder, HOUSE, **kw)["screen"]

    def test_finished_house_is_done(self):
        self.assertEqual(self.screen(), houses.DONE)

    def test_sealed_review_and_no_request_is_the_pdf_screen(self):
        self.drop("05 request")
        self.assertEqual(self.screen(), houses.PDF)

    def test_variance_and_no_review_is_the_difference(self):
        self.drop("05 request"); self.drop("04 review")
        self.assertEqual(self.screen(), houses.DIFFERENCE)

    def test_sealed_read_back_and_no_variance_goes_to_compare(self):
        for stage in ("05 request", "04 review", "03 compare"):
            self.drop(stage)
        self.assertEqual(self.screen(), houses.COMPARE)

    def test_draft_read_back_is_the_check_screen(self):
        for stage in ("05 request", "04 review", "03 compare"):
            self.drop(stage)
        path = self.folder.stage("02 read", HOUSE) / "read-back-1.md"
        seal = self.folder.script("02 read", "seal")
        draft = seal.STATUS.sub("status: draft", seal.unsealed(path.read_text(encoding="utf-8")), count=1)
        path.write_text(draft, encoding="utf-8")
        self.assertEqual(self.screen(), houses.CHECK)

    def test_intake_and_no_read_back_is_reading(self):
        for stage in ("05 request", "04 review", "03 compare", "02 read"):
            self.drop(stage)
        self.assertEqual(self.screen(), houses.READING)

    def test_a_running_job_shows_busy_on_its_screen(self):
        state = houses.stand(self.folder, HOUSE, running=True)
        self.assertTrue(state["busy"])
        self.assertEqual(state["screen"], houses.DONE)

    def test_unknown_house_is_new(self):
        self.assertEqual(houses.stand(self.folder, "no-such-house")["screen"], houses.NEW)

    def test_read_back_changed_after_the_yes_stops_the_house(self):
        path = self.folder.stage("02 read", HOUSE) / "read-back-1.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nedited\n", encoding="utf-8")
        state = houses.stand(self.folder, HOUSE)
        self.assertEqual(state["screen"], houses.STOPPED)
        self.assertTrue(state["reason"])

    def test_review_changed_after_the_yes_stops_the_house(self):
        self.drop("05 request")
        path = self.folder.stage("04 review", HOUSE) / "review-1.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nedited\n", encoding="utf-8")
        self.assertEqual(self.screen(), houses.STOPPED)

    def test_folder_with_no_houses_lists_none(self):
        empty = self.tmp / "empty"
        (empty / "reference").mkdir(parents=True)
        shutil.copy(self.folder.root / "reference" / "contractor.md", empty / "reference")
        (empty / "01 intake").mkdir()
        self.assertEqual(houses.all_houses(Folder(empty)), [])

    def test_folder_that_is_not_set_up_is_refused(self):
        with self.assertRaises(SystemExit):
            Folder(self.tmp)


if __name__ == "__main__":
    unittest.main()
