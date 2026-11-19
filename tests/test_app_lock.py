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
        # The sample POs are uploaded as a new house, so the copy must not already hold them.
        shutil.rmtree(self.folder.stage("01 intake", "77-mockup-drive"))
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

    def test_notes_are_named_so_the_request_knows_them(self):
        held = self.held(notes=[("image.jpg", b"a"), ("image.jpg", b"b"), ("scan.pdf", b"%PDF c")])
        intake = self.folder.stage("01 intake", lock.lock(self.folder, held["id"], {}, today=DAY))
        self.assertEqual(sorted(p.name for p in intake.glob("site-notes*")),
                         ["site-notes-2.jpg", "site-notes.jpg", "site-notes.pdf"])
        self.assertEqual((intake / "site-notes-2.jpg").read_bytes(), b"b")

    def test_po_photo_is_wrapped_in_a_pdf_with_the_image_unchanged(self):
        import pymupdf
        page = pymupdf.open()
        page.new_page(width=200, height=100)
        png = page[0].get_pixmap().tobytes("png")
        held = self.held(pos=po_files() + [("IMG_0001.png", png)])
        intake = self.folder.stage("01 intake", lock.lock(self.folder, held["id"], {}, today=DAY))
        wrapped = intake / "IMG_0001 (PO photo).pdf"
        with pymupdf.open(wrapped) as doc:
            self.assertEqual(len(doc), 1)
            self.assertEqual(doc.extract_image(doc[0].get_images()[0][0])["image"], png)

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

    def test_same_po_twice_in_one_upload_is_refused(self):
        twice = po_files()[:1] * 2
        with self.assertRaises(lock.Refused) as caught:
            self.held(pos=[twice[0], ("copy.html", twice[1][1])])
        self.assertIn("are the same file", str(caught.exception))

    def read_once(self, house):
        with mock.patch.dict(os.environ, {"STANDIN_MODE": "draft"}):
            jobs = Jobs(self.folder)
            steps.start_read(self.folder, jobs, house)
            self.assertTrue(jobs.wait(house))

    def test_po_already_in_a_house_that_was_read_is_refused(self):
        house = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        self.read_once(house)
        with self.assertRaises(lock.Refused) as caught:
            self.held(address="77 Mockup Drive")
        self.assertIn(f"already in {house} (77 Mockup Drive)", str(caught.exception))

    def test_starting_again_after_a_stopped_read_replaces_the_old_house(self):
        old = lock.lock(self.folder, self.held()["id"], {}, today=DAY)  # its read never wrote a read-back
        new = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        self.assertNotEqual(old, new)
        self.assertEqual(lock.replaced_by(self.folder, old), new)
        with self.assertRaises(steps.Stopped) as caught:
            steps.start_read(self.folder, Jobs(self.folder), old)
        self.assertIn(f"as {new}", str(caught.exception))
        with self.assertRaises(lock.Refused):  # a third copy: the old house is replaced, the new one stands
            self.read_once(new)
            self.held()

    def test_a_hidden_house_does_not_show_or_block_a_new_upload(self):
        old = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        self.read_once(old)  # past the read, so it would block the same POs
        (self.folder.root / "_app" / "hidden.json").write_text(json.dumps({"houses": [old]}), encoding="utf-8")
        self.assertNotIn(old, self.folder.houses())
        new = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        self.assertNotEqual(new, old)
        self.assertTrue(self.folder.stage("02 read", old).is_dir())  # its records stay

    def test_a_second_restart_also_works(self):
        first = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        second = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        third = lock.lock(self.folder, self.held()["id"], {}, today=DAY)
        self.assertEqual((lock.replaced_by(self.folder, first), lock.replaced_by(self.folder, second)), (second, third))
        self.assertIsNone(lock.replaced_by(self.folder, third))

    def test_notes_file_twice_or_a_po_also_as_notes_is_refused(self):
        for notes in ([("a.jpg", b"same"), ("b.jpg", b"same")], [("po.html", po_files()[0][1])]):
            with self.subTest(notes=[n for n, _ in notes]), self.assertRaises(lock.Refused):
                self.held(notes=notes)

    def test_the_same_po_photo_cannot_go_in_two_houses(self):
        import pymupdf
        page = pymupdf.open()
        page.new_page(width=200, height=100)
        png = page[0].get_pixmap().tobytes("png")
        house = lock.lock(self.folder, self.held(pos=[("IMG_1.png", png)])["id"], {}, today=DAY)
        self.read_once(house)
        with self.assertRaises(lock.Refused):
            self.held(pos=[("IMG_1 copy.png", png)])

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
