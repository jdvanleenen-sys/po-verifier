"""The phone app's runner, step 5, and the whole house through the runner: 77 Mockup Drive from its
sealed read-back to a numbered request whose money matches the house's sealed answer key
($972.00 before tax, $48.60 tax, $1,020.60 requested). The agent is a stand-in that runs the
folder's own build on the house's filled layout."""
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import config  # noqa: E402
import houses  # noqa: E402
import request_pdf  # noqa: E402
import steps  # noqa: E402
from folder import Folder  # noqa: E402
from jobs import Jobs  # noqa: E402

HOUSE = "77-mockup-drive"
LEAVE_OUT = shutil.ignore_patterns(".git", ".venv", "tests", "docs", "_for-testers", "__pycache__", "real-*", "app")
STANDIN = [sys.executable, str(ROOT / "tests" / "app_standin_agent.py")]
KEY_DAY = date(2026, 10, 17)  # the layout's prepared date; the review's yes may not be after it


class Request(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import pymupdf  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("needs PyMuPDF")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT, self.tmp / "f", ignore=LEAVE_OUT)
        self.folder = Folder(self.tmp / "f")
        for stage in ("03 compare", "04 review", "05 request"):
            shutil.rmtree(self.folder.stage(stage, HOUSE))
        patcher = mock.patch.object(config, "AGENT_COMMAND", STANDIN)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.jobs = Jobs(self.folder)
        steps.run_compare(self.folder, HOUSE)
        steps.review_yes(self.folder, HOUSE, {"7": {"on": True, "epo": ""}}, today=KEY_DAY)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, notes="yes"):
        request_pdf.save_notes(self.folder, HOUSE, notes)
        self.assertTrue(steps.start_request(self.folder, self.jobs, HOUSE))
        self.assertTrue(self.jobs.wait(HOUSE, 120))

    def test_whole_house_to_a_numbered_request_matching_the_key(self):
        self.build()
        shown = request_pdf.draft(self.folder, HOUSE)
        self.assertTrue(shown["passed"], shown["checks"])
        self.assertEqual(steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY), "vpo-request-1.pdf")
        self.assertEqual(houses.stand(self.folder, HOUSE)["screen"], houses.DONE)
        import pymupdf
        with pymupdf.open(self.folder.stage("05 request", HOUSE) / "vpo-request-1.pdf") as doc:
            first = doc[0].get_text()
        for figure in ("$972.00", "$48.60", "$1,020.60"):
            self.assertIn(figure, first)
        check = (self.folder.stage("05 request", HOUSE) / "request-check-1.md").read_text(encoding="utf-8")
        self.assertIn("- Answer: yes, to vpo-request-1.pdf as shown\n- Name: Sam\n- Date: 2026-10-17\n- sent:\n", check)

    def test_second_approve_gives_the_same_number_once(self):
        self.build()
        first = steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY)
        self.assertEqual(steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY), first)
        self.assertEqual(len(list(self.folder.stage("05 request", HOUSE).glob("vpo-request-*.pdf"))), 1)

    def test_second_approve_writes_a_missing_yes_to_send(self):
        self.build()
        steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY)
        check = self.folder.stage("05 request", HOUSE) / "request-check-1.md"
        check.write_text(check.read_text(encoding="utf-8").replace("- Answer: yes, to vpo-request-1.pdf as shown", "- Answer:"),
                         encoding="utf-8", newline="\n")
        self.assertTrue(request_pdf.yes_missing(check))
        steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY)
        self.assertFalse(request_pdf.yes_missing(check))

    def test_approve_before_a_passing_draft_is_refused(self):
        with self.assertRaises(steps.Stopped):
            steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY)
        self.assertIsNone(request_pdf.numbered(self.folder, HOUSE))

    def test_failed_check_is_never_numbered(self):
        self.build(notes="no")  # the filled layout names the notes, so check 5 fails
        self.assertFalse(request_pdf.draft(self.folder, HOUSE)["passed"])
        with self.assertRaises(steps.Stopped):
            steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY)
        self.assertIsNone(request_pdf.numbered(self.folder, HOUSE))

    def test_a_check_that_is_not_pass_stops_before_approve(self):
        self.build()
        checks = self.folder.stage("05 request", "drafts") / HOUSE / "script-checks.md"
        text = checks.read_text(encoding="utf-8")
        checks.write_text(text.replace("5. Every proof document attached: pass:", "5. Every proof document attached: cannot check:"),
                          encoding="utf-8")
        self.assertFalse(request_pdf.draft(self.folder, HOUSE)["passed"])

    def test_draft_from_before_the_current_review_is_never_shown(self):
        draft = self.folder.stage("05 request", "drafts") / HOUSE
        old = __import__("time").time() - 3600
        for name in ("vpo-request.pdf", "script-checks.md"):
            if (draft / name).exists():
                __import__("os").utime(draft / name, (old, old))
        shown = request_pdf.draft(self.folder, HOUSE)
        self.assertEqual((shown["pdf"], shown["passed"]), (None, False))

    def test_request_needs_the_notes_answer_first(self):
        with self.assertRaises(steps.Stopped):
            steps.start_request(self.folder, self.jobs, HOUSE)

    def test_shared_notes_page_needs_his_yes_in_those_words(self):
        info = self.folder.stage("01 intake", HOUSE) / "house-info.md"
        original = info.read_bytes()
        info.write_text(info.read_text(encoding="utf-8") + "\nIt covers two houses.\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            request_pdf.save_notes(self.folder, HOUSE, "yes")
        self.assertEqual(request_pdf.save_notes(self.folder, HOUSE, "yes-other-house"), "yes-other-house")
        info.write_bytes(original)

    def test_restart_mid_house_resumes_at_the_pdf_screen(self):
        self.assertEqual(houses.stand(self.folder, HOUSE)["screen"], houses.PDF)
        self.assertEqual(houses.stand(Folder(self.folder.root), HOUSE)["screen"], houses.PDF)

    def test_mark_sent(self):
        self.build()
        steps.approve(self.folder, self.jobs, HOUSE, today=KEY_DAY)
        check = self.folder.stage("05 request", HOUSE) / "request-check-1.md"
        request_pdf.mark_sent(check)
        self.assertIn("- sent: yes", check.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
