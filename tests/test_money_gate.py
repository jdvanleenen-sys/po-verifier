"""The money gate, proved on planted mistakes. Run from the repo root:

    python -m unittest discover -s tests -v

Uses only 77 Mockup Drive (the finished worked example), never the test house, so it gives
nothing away. Each planted mistake must be refused; each clean case must pass. No browser needed.
"""
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import money  # noqa: E402
import verify  # noqa: E402

HOUSE = "77-mockup-drive"
RECORDS = {"read-back": ROOT / "02 read" / HOUSE / "read-back-1.md",
           "variance": ROOT / "03 compare" / HOUSE / "variance-1.md",
           "review": ROOT / "04 review" / HOUSE / "review-1.md"}
REAL_PDF = ROOT / "05 request" / HOUSE / "vpo-request-1.pdf"
NOTES_MARKER = "77 Mockup Dr / lot 24"


def texts(**changes):
    """77's three records, with (old, new) replacements applied to the named record."""
    out = {k: money.read_text(p) for k, p in RECORDS.items()}
    for key, (old, new) in changes.items():
        assert old in out[key], f"planted change not found in {key}: {old}"
        out[key] = out[key].replace(old, new, 1)
    return out


def expected():
    exp, problems = money.expected_request(texts())
    assert not problems, problems
    return exp


def proof(notes=True):
    exp = expected()
    return {"po_numbers": exp["po_numbers"], "epo_names": exp["epo_names"], "notes": notes,
            "notes_marker": NOTES_MARKER}


def page_texts(path=REAL_PDF):
    with pymupdf.open(path) as doc:
        return [p.get_text() for p in doc]


def write_pdf(folder, pages):
    """A PDF whose pages carry exactly these texts (a forged or edited request)."""
    path = Path(folder) / "forged.pdf"
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(36, 36, 576, 806), text, fontsize=6)
    doc.save(path)
    return path


def failed(lines):
    return [l for l in lines if ": fail:" in l]


class Records(unittest.TestCase):
    def test_clean_records_give_the_known_request(self):
        house = expected()["house"]
        self.assertEqual((house["before"], house["tax"], house["total"]),
                         (Decimal("972.00"), Decimal("48.60"), Decimal("1020.60")))

    def assertProblem(self, words, **changes):
        _, problems = money.expected_request(texts(**changes))
        self.assertTrue(any(words in p for p in problems), problems)

    def test_unapproved_read_back_is_refused(self):
        self.assertProblem("read-back does not carry", **{"read-back": ("status: approved", "status: draft")})

    def test_review_row_without_decision_is_refused(self):
        self.assertProblem("no on/off decision", review=("off (not chosen)", "maybe"))

    def test_variance_that_disagrees_with_read_back_is_refused(self):
        self.assertProblem("the read-back gives", variance=("+$300.00", "+$3,000.00"))

    def test_measured_qty_not_in_sams_notes_is_refused(self):
        self.assertProblem("not in Sam's notes", variance=("| 12 | $720.00", "| 13 | $780.00"))

    def test_row_missing_from_variance_is_refused(self):
        line = next(l for l in texts()["variance"].splitlines() if "Railing, wood" in l)
        self.assertProblem("missing from the variance", variance=(line + "\n", ""))

    def test_utf16_and_bom_records_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i, encoding in enumerate(("utf-16", "utf-8-sig")):
                path = Path(tmp) / f"r{i}.md"
                path.write_text(texts()["review"], encoding=encoding)
                self.assertTrue(money.approved(money.read_text(path)))


class Pdf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def check(self, path, notes=True):
        return verify.run_checks(path, expected(), proof(notes))

    def edited(self, page, old, new):
        pages = page_texts()
        self.assertIn(old, pages[page])
        pages[page] = pages[page].replace(old, new)
        return write_pdf(self.tmp, pages)

    def test_real_request_passes_all_six(self):
        self.assertEqual(failed(self.check(REAL_PDF)), [])

    def test_one_byte_file_is_refused(self):
        fake = Path(self.tmp) / "x.pdf"
        fake.write_bytes(b"x")
        self.assertEqual(len(failed(self.check(fake))), 6)

    def test_layout_sample_with_no_proof_is_refused(self):
        lines = self.check(ROOT / "reference" / "request-layout-sample.pdf")
        self.assertTrue(any(l.startswith("5.") for l in failed(lines)), lines)

    def test_wrong_house_total_is_refused(self):
        lines = self.check(self.edited(0, "$1,020.60", "$1,520.60"))
        self.assertTrue(any(l.startswith("4.") for l in failed(lines)), lines)

    def test_wrong_difference_is_refused(self):
        lines = self.check(self.edited(0, "+$300.00", "+$330.00"))
        self.assertTrue(any(l.startswith("2.") for l in failed(lines)), lines)

    def test_row_sam_chose_off_is_refused(self):
        lines = self.check(self.edited(0, "8' doors and trim", "8' doors and trim Stringer, inside or outside"))
        self.assertTrue(any(l.startswith("1.") for l in failed(lines)), lines)

    def test_wrong_page_count_is_refused(self):
        lines = self.check(self.edited(0, "page 1 of 1", "page 1 of 2"))
        self.assertTrue(any(l.startswith("6.") for l in failed(lines)), lines)

    def test_missing_po_in_proof_is_refused(self):
        pages = [p for p in page_texts() if "02402401/041" not in p or "Checked and approved by" in p]
        lines = self.check(write_pdf(self.tmp, pages))
        self.assertTrue(any(l.startswith("5.") for l in failed(lines)), lines)

    def test_notes_attached_when_sam_said_no_is_refused(self):
        lines = self.check(REAL_PDF, notes=False)
        self.assertTrue(any(l.startswith("5.") for l in failed(lines)), lines)


if __name__ == "__main__":
    unittest.main()
