"""The request and intake gaps found by the 2026-11-09 attack on a real house. Run from the repo root:

    python -m unittest discover -s tests -v

Each was accepted before: a request numbered under the wrong trade contractor or builder (a00,
a34, a35); a draft PDF changed between build and commit (a31); a second request numbered from the
same review (a32); a PO changed, saved twice or another house's PO added to intake after the read
(a36, a37, a38); a traceback on a bad date (a42); a review naming a missing variance reported as
"no variance" (a26). Made-up data only.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
sys.path.insert(0, str(ROOT / "02 read"))
import build_request  # noqa: E402
import contractor  # noqa: E402
import header_checks  # noqa: E402
import house_checks  # noqa: E402
import intake_read  # noqa: E402
import verify  # noqa: E402

SAMPLE = ROOT / "05 request" / "77-mockup-drive" / "vpo-request-1.pdf"
SETUP = {"name": "Sample Painting Co.", "vendor": "V00999", "builders": "Sample Builder Ltd., through SupplyPro",
         "shown": "Sample Painting Co. (V00999)"}
POS = """## POs read
| PO number | Cost code | Vendor | Subtotal |
|---|---|---|---|
| ABC-1/012 | PAIN-005 | {vendor} | $100.00 |
"""


def passes(result):
    return ": pass:" in result


def sample_pages(old=None, new=None):
    pages = verify.split_request(verify.pdf_pages(SAMPLE))[0]
    if old is None:
        return pages
    assert old in pages[0], old
    return [pages[0].replace(old, new, 1)] + pages[1:]


class TheContractor(unittest.TestCase):
    def test_po_to_another_vendor_is_refused(self):
        problems = contractor.vendor_problems(POS.format(vendor="Other Brush Ltd., V00777"), SETUP)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("00 setup", problems[0])

    def test_po_to_this_vendor_passes(self):
        self.assertEqual(contractor.vendor_problems(POS.format(vendor="Sample Painting Co., V00999 (attn)"), SETUP), [])

    def test_a_longer_vendor_number_is_not_a_match(self):
        self.assertTrue(contractor.vendor_problems(POS.format(vendor="Sample Painting Co., V009990"), SETUP))

    def test_setup_is_read_from_the_folder(self):
        who = contractor.read()
        self.assertEqual(who["shown"], "Sample Painting Co. (V00999)")
        self.assertIn("Sample Builder Ltd.", who["builders"])


class TheHeader(unittest.TestCase):
    SPEC = {"document": "VR-0001", "job_numbers": None, "job_names": ["MKR-02402401-77 Mockup Drive"],
            "contractor": SETUP["shown"], "builders": SETUP["builders"]}

    def check(self, pages):
        return verify.check_pages(pages, self.SPEC)

    def test_sample_passes(self):
        self.assertTrue(passes(self.check(sample_pages())), self.check(sample_pages()))

    def test_unconfirmed_contractor_fails(self):
        pages = sample_pages("Sample Painting Co. (V00999)", "NOT CONFIRMED: POs name Other Brush (V00777)")
        self.assertFalse(passes(self.check(pages)))

    def test_another_contractor_fails(self):
        pages = sample_pages("Sample Painting Co. (V00999)", "Other Brush Ltd. (V00777)")
        self.assertFalse(passes(self.check(pages)))

    def test_another_builder_fails(self):
        pages = sample_pages("Sample Builder Ltd.", "Other Homes Inc.")
        self.assertFalse(passes(self.check(pages)))

    def test_bad_date_is_plain_words(self):
        problems = header_checks.measured_problems("measured on site november 30, 2026", "2026-11-31")
        self.assertEqual(len(problems), 1)
        self.assertIn("not a real date", problems[0])

    def test_document_number_message_does_not_invite_renumbering(self):
        result = verify.check_pages(sample_pages(), dict(self.SPEC, document="VR-0002"))
        self.assertIn("never typed by hand", result)

    def test_foreign_job_name_message_says_check_the_po(self):
        result = verify.check_pages(sample_pages(), dict(self.SPEC, job_names=["MKR-02402409-14 Example Crescent"]))
        self.assertIn("comes out of intake", result)


class TheIntake(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "po.html").write_text("<p>qty 16</p>", encoding="utf-8")
        (self.dir / "notes.jpg").write_bytes(b"\xff\xd8photo")
        self.grid = "\n".join(intake_read.section(self.dir))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_unchanged_passes(self):
        self.assertEqual(intake_read.problems(self.dir, self.grid, "h"), [])

    def test_one_byte_changed_is_refused(self):
        (self.dir / "po.html").write_text("<p>qty 18</p>", encoding="utf-8")
        self.assertIn("changed after it was read", intake_read.problems(self.dir, self.grid, "h")[0])

    def test_a_file_added_is_refused(self):
        (self.dir / "po resent.html").write_text("<p>qty 16</p> ", encoding="utf-8")
        self.assertIn("was added after the read", intake_read.problems(self.dir, self.grid, "h")[0])

    def test_a_file_gone_is_refused(self):
        (self.dir / "notes.jpg").unlink()
        self.assertIn("is gone", intake_read.problems(self.dir, self.grid, "h")[0])

    def test_a_grid_without_the_table_is_refused(self):
        self.assertIn("no Intake read table", intake_read.problems(self.dir, "## Row grid", "h")[0])


class TheDraftAndTheReview(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_pdf_changed_after_build_is_refused(self):
        pdf = self.dir / "vpo-request.pdf"
        pdf.write_bytes(b"%PDF built")
        checks = f"notes: yes\npdf sha256: {house_checks.sha256(pdf)}\n"
        self.assertIsNone(house_checks.pdf_problem(pdf, checks))
        pdf.write_bytes(b"%PDF built, then a payee line added")
        self.assertIn("changed after it was built", house_checks.pdf_problem(pdf, checks))
        self.assertIn("does not record", house_checks.pdf_problem(pdf, "notes: yes\n"))

    def test_a_second_request_from_one_review_is_found(self):
        (self.dir / "request-check-1.md").write_text("---\nfrom review: 04 review/h/review-1.md\n---\n", encoding="utf-8")
        self.assertEqual(house_checks.review_used(self.dir, "04 review/h/review-1.md"), "vpo-request-1.pdf")
        self.assertIsNone(house_checks.review_used(self.dir, "04 review/h/review-2.md"))


class AMissingVariance(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "04 review" / "h").mkdir(parents=True)
        (self.tmp / "03 compare" / "h").mkdir(parents=True)
        (self.tmp / "03 compare" / "h" / "variance-1.md").write_text("x", encoding="utf-8")
        (self.tmp / "04 review" / "h" / "review-1.md").write_text(
            "---\nfrom: 03 compare/h/variance-9.md\n---\n", encoding="utf-8")
        self.old, build_request.ROOT = build_request.ROOT, self.tmp

    def tearDown(self):
        build_request.ROOT = self.old
        shutil.rmtree(self.tmp)

    def test_the_missing_file_is_named(self):
        with self.assertRaises(SystemExit) as stop:
            build_request.records("h")
        self.assertIn("variance-9.md", str(stop.exception.code))


if __name__ == "__main__":
    unittest.main()
