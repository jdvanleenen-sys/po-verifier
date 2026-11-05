"""Site notes of any kind reach the request: typed, photos, a voice-memo transcript. Run from the repo root:

    python -m unittest discover -s tests -v

Sam can attach all of them, none, or only the pages he names. A page he left out must not be in
the PDF, and a page he named must be. No browser needed: the PDF text is laid out by hand.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import build_request  # noqa: E402
import printing  # noqa: E402
import verify  # noqa: E402

HOUSE = "9-notes-test-way"


class NotesInIntake(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        folder = self.tmp / "01 intake" / HOUSE
        folder.mkdir(parents=True)
        for name in ("PO A-1-012.html", "site-notes-photo-1.jpg", "site-notes-photo-2.jpg",
                     "voice-memo-transcript.txt", "house-info.md", "random.docx"):
            (folder / name).write_bytes(b"x" if not name.endswith(".html") else b"<html>po</html>")
        self.old_root = build_request.ROOT
        build_request.ROOT = self.tmp

    def tearDown(self):
        build_request.ROOT = self.old_root
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_photos_and_voice_memo_count_as_notes(self):
        docs, notes, others = build_request.intake(HOUSE)
        self.assertEqual([p.name for p in docs], ["PO A-1-012.html"])
        self.assertEqual(sorted(p.name for p in notes),
                         ["site-notes-photo-1.jpg", "site-notes-photo-2.jpg", "voice-memo-transcript.txt"])
        self.assertEqual(len(others), 1)
        self.assertIn("random.docx", others[0])

    def test_sam_can_name_only_some_pages(self):
        _, notes, _ = build_request.intake(HOUSE)
        chosen = build_request.choose_notes(notes, "only:site-notes-photo-1.jpg")
        self.assertEqual([p.name for p in chosen], ["site-notes-photo-1.jpg"])
        self.assertEqual(build_request.choose_notes(notes, "no"), [])
        self.assertEqual(len(build_request.choose_notes(notes, "yes")), 3)

    def test_naming_a_page_that_is_not_there_stops(self):
        _, notes, _ = build_request.intake(HOUSE)
        with self.assertRaises(SystemExit):
            build_request.choose_notes(notes, "only:site-notes-photo-9.jpg")


class NotesPage(unittest.TestCase):
    def test_a_photo_page_shows_its_name_and_the_image(self):
        page = printing.notes_page_html(Path("C:/x/site-notes-photo-1.jpg"))
        self.assertIn("site-notes-photo-1.jpg", page)
        self.assertIn("<img", page)

    def test_a_text_page_shows_its_name_and_the_text_escaped(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "voice-memo-transcript.txt"
            path.write_text("doors <twelve> & two", encoding="utf-8")
            page = printing.notes_page_html(path)
            self.assertIn("voice-memo-transcript.txt", page)
            self.assertIn("doors &lt;twelve&gt; &amp; two", page)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def proof(attached, left_out):
    return {"po_numbers": ["A-1/012"], "epo_names": [], "notes_attached": attached, "notes_left_out": left_out}


class ProofCheck(unittest.TestCase):
    PAGES = ["PO A-1/012 the po", "site-notes-photo-1.jpg (photo)"]

    def test_named_page_attached_and_other_left_out_passes(self):
        result = verify.check_proof(self.PAGES, proof(["site-notes-photo-1.jpg"], ["site-notes-photo-2.jpg"]))
        self.assertIn(": pass:", result)

    def test_page_sam_left_out_but_attached_fails(self):
        result = verify.check_proof(self.PAGES, proof([], ["site-notes-photo-1.jpg"]))
        self.assertIn(": fail:", result)

    def test_page_sam_named_but_missing_fails(self):
        result = verify.check_proof(self.PAGES, proof(["site-notes-photo-1.jpg", "voice-memo-transcript.txt"], []))
        self.assertIn(": fail:", result)


if __name__ == "__main__":
    unittest.main()
