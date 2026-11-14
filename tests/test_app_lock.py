"""The phone app's runner, step 2: hold the uploads, ask before the read, lock them into intake, and
run the read as one background job per house. The agent is a stand-in that calls no model."""
import json
import os
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
import lock  # noqa: E402
import steps  # noqa: E402
from folder import Folder  # noqa: E402
from jobs import Jobs  # noqa: E402

SAMPLE = ROOT / "01 intake" / "77-mockup-drive"
LEAVE_OUT = shutil.ignore_patterns(".git", ".venv", "tests", "docs", "_for-testers", "__pycache__", "real-*", "app")
STANDIN = [sys.executable, str(ROOT / "tests" / "app_standin_agent.py")]
DAY = date(2026, 11, 14)


def po_files():
    return [(p.name, p.read_bytes()) for p in sorted(SAMPLE.glob("PO *.html"))]


def notes_files():
    return [("image.jpg", b"\xff\xd8 not a real photo")]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT, self.tmp / "f", ignore=LEAVE_OUT)
        self.folder = Folder(self.tmp / "f")
        patcher = mock.patch.object(config, "AGENT_COMMAND", STANDIN)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def held(self, address="77 Mockup Drive", measured="2026-11-12", pos=None, notes=None, covers=False):
        return lock.hold(self.folder, address, measured, covers, po_files() if pos is None else pos,
                         notes_files() if notes is None else notes)


class Hold(Base):
    def test_matching_address_asks_nothing(self):
        self.assertEqual(self.held()["questions"], [])

    def test_short_form_of_the_street_matches(self):
        self.assertEqual(self.held(address="77 Mockup Dr")["questions"], [])

    def test_other_address_asks_sam_before_the_read(self):
        questions = self.held(address="501 Example Terrace")["questions"]
        self.assertEqual([q["id"] for q in questions], ["address"])
        self.assertIn('"77 Mockup Drive"', questions[0]["ask"])

    def test_nothing_reaches_intake_before_lock(self):
        self.held()
        self.assertFalse(list(self.folder.stage("01 intake").glob("real-*")))

    def test_refusals_in_plain_words(self):
        cases = [dict(address=" "), dict(pos=[]), dict(notes=[]), dict(measured="last week"),
                 dict(pos=[("po.docx", b"x")]), dict(pos=[("po.html", b"")])]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(lock.Refused):
                self.held(**case)

    def test_too_big_a_file_is_refused(self):
        with mock.patch.object(config, "MAX_FILE_BYTES", 10), self.assertRaises(lock.Refused):
            self.held()


class Lock(Base):
    def test_lock_writes_intake_once_with_house_info(self):
        house = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        intake = self.folder.stage("01 intake", house)
        self.assertEqual(house, "real-1")
        for name, data in po_files():
            self.assertEqual((intake / name).read_bytes(), data)
        info = (intake / "house-info.md").read_text(encoding="utf-8")
        self.assertIn("- Date measured: 2026-11-12", info)
        self.assertIn("- Date dropped in: 2026-11-14", info)

    def test_two_photos_with_one_name_both_kept(self):
        held = self.held(notes=[("image.jpg", b"a"), ("image.jpg", b"b")])
        intake = self.folder.stage("01 intake", lock.lock(self.folder, held["id"], {}, today=DAY))
        self.assertEqual(sorted(p.name for p in intake.glob("image*")), ["image-2.jpg", "image.jpg"])

    def test_not_recorded_leaves_the_line_blank_for_the_read_back(self):
        held = self.held(measured="Not recorded", covers=True)
        info = (self.folder.stage("01 intake", lock.lock(self.folder, held["id"], {}, today=DAY))
                / "house-info.md").read_text(encoding="utf-8")
        self.assertIn("- Date measured: \n", info)
        self.assertIn("It covers two houses", info)

    def test_unanswered_or_no_address_question_locks_nothing(self):
        held = self.held(address="501 Example Terrace")
        for answers in ({}, {"address": "maybe"}, {"address": "no"}):
            with self.subTest(answers=answers), self.assertRaises(lock.Refused):
                lock.lock(self.folder, held["id"], answers, today=DAY)
        self.assertFalse(list(self.folder.stage("01 intake").glob("real-*")))

    def test_a_second_lock_of_the_same_upload_is_refused(self):
        held = self.held()
        lock.lock(self.folder, held["id"], {}, today=DAY)
        with self.assertRaises(lock.Refused):
            lock.lock(self.folder, held["id"], {}, today=DAY)

    def test_unknown_or_odd_upload_id_is_refused(self):
        for held_id in ("0" * 16, "../../etc", ""):
            with self.subTest(held_id=held_id), self.assertRaises(lock.Refused):
                lock.lock(self.folder, held_id, {}, today=DAY)

    def test_next_house_number_skips_used_ones(self):
        self.folder.stage("02 read", "real-1").mkdir(parents=True)
        self.assertEqual(lock.lock(self.folder, self.held()["id"], {}, today=DAY), "real-2")


class Read(Base):
    def locked(self, **kw):
        held = self.held(**kw)
        answers = {"address": "yes"} if held["questions"] else {}
        return lock.lock(self.folder, held["id"], answers, today=DAY)

    def run_read(self, house, mode="draft"):
        out = self.tmp / "prompt.txt"
        with mock.patch.dict(os.environ, {"STANDIN_MODE": mode, "STANDIN_PROMPT_OUT": str(out)}):
            jobs = Jobs(self.folder)
            self.assertTrue(steps.start_read(self.folder, jobs, house))
            self.assertTrue(jobs.wait(house))
        return jobs, (out.read_text(encoding="utf-8") if out.exists() else "")

    def test_read_reaches_the_check_screen(self):
        house = self.locked()
        jobs, _ = self.run_read(house)
        self.assertEqual(jobs.status(house)["status"], "done")
        self.assertEqual(houses.stand(self.folder, house)["screen"], houses.CHECK)

    def test_answers_before_the_read_go_in_the_prompt(self):
        house = self.locked(address="501 Example Terrace", measured="not recorded")
        _, text = self.run_read(house)
        self.assertIn("Date measured: not recorded (Sam, 2026-11-14)", text)
        self.assertIn('"Yes, these are the POs for 501 Example Terrace."', text)
        self.assertNotIn("{", text)

    def test_reader_that_stops_leaves_the_house_reading_with_its_reason(self):
        house = self.locked()
        jobs, _ = self.run_read(house, "stopped")
        self.assertEqual(jobs.status(house)["status"], "failed")
        self.assertIn("STOPPED", jobs.status(house)["line"])
        self.assertEqual(houses.stand(self.folder, house)["screen"], houses.READING)

    def test_reader_answer_that_is_not_json_fails_plainly(self):
        house = self.locked()
        jobs, _ = self.run_read(house, "garbage")
        self.assertEqual(jobs.status(house)["status"], "failed")

    def test_second_start_while_reading_does_nothing_and_stop_ends_it(self):
        house = self.locked()
        with mock.patch.dict(os.environ, {"STANDIN_MODE": "slow"}):
            jobs = Jobs(self.folder)
            self.assertTrue(steps.start_read(self.folder, jobs, house))
            self.assertFalse(steps.start_read(self.folder, jobs, house))
            self.assertTrue(jobs.stop(house))
            self.assertTrue(jobs.wait(house, 20))
        self.assertEqual(jobs.status(house)["status"], "stopped")

    def test_time_limit_stops_the_read(self):
        house = self.locked()
        with mock.patch.dict(os.environ, {"STANDIN_MODE": "slow"}), \
                mock.patch.object(config, "READ_LIMIT_SECONDS", 2):
            jobs = Jobs(self.folder)
            steps.start_read(self.folder, jobs, house)
            self.assertTrue(jobs.wait(house, 20))
        self.assertIn("ran past", jobs.status(house)["line"])

    def test_restart_mid_read_shows_interrupted(self):
        house = self.locked()
        record = self.folder.root / config.APP_DIR / house / "job.json"
        record.write_text(json.dumps({"kind": "read", "status": "running"}), encoding="utf-8")
        self.assertEqual(Jobs(self.folder).status(house)["status"], "interrupted")

    def test_read_refused_once_past_the_read(self):
        house = self.locked()
        self.run_read(house)
        with self.assertRaises(steps.Stopped):
            steps.start_read(self.folder, Jobs(self.folder), house)

    def test_house_not_locked_by_the_app_is_refused(self):
        with self.assertRaises(steps.Stopped):
            steps.start_read(self.folder, Jobs(self.folder), "14-example-crescent")


if __name__ == "__main__":
    unittest.main()
