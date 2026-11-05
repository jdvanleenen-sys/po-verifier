"""The request's header names the right job and the number the commit will give. Run from the repo root:

    python -m unittest discover -s tests -v

Found by the 2026-11-05 test loop: a request numbered 3 that printed VR-0001, and a wrong job name,
lot or house number in the header, all passed. The text is the committed 77 Mockup Drive request.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import build_request  # noqa: E402
import verify  # noqa: E402

PDF = ROOT / "05 request" / "77-mockup-drive" / "vpo-request-1.pdf"


def passes(result):
    return ": pass:" in result


def request_pages():
    return verify.split_request(verify.pdf_pages(PDF))[0]


def edited(old, new):
    pages = request_pages()
    assert old in pages[0], old
    return [pages[0].replace(old, new, 1)] + pages[1:]


class HeaderFromIntake(unittest.TestCase):
    def test_header_spec_reads_house_info_and_po_job_names(self):
        spec = build_request.header_spec("77-mockup-drive", 1)
        self.assertEqual(spec["document"], "VR-0001")
        self.assertEqual(sorted(spec["job_numbers"]), ["24", "3", "77"])
        self.assertEqual(spec["job_names"], ["MKR-02402401-77 Mockup Drive"])


class HeaderOnTheRequest(unittest.TestCase):
    SPEC = {"document": "VR-0001", "job_numbers": ["77", "24", "3"], "job_names": ["MKR-02402401-77 Mockup Drive"]}

    def check(self, pages, spec=None):
        return verify.check_pages(pages, spec or self.SPEC)

    def test_sample_passes(self):
        self.assertTrue(passes(self.check(request_pages())), self.check(request_pages()))

    def test_stale_document_number_fails(self):
        result = self.check(request_pages(), dict(self.SPEC, document="VR-0003"))
        self.assertFalse(passes(result))
        self.assertIn("VR-0003", result)

    def test_wrong_job_name_fails(self):
        pages = edited("MKR-02402401-77 Mockup Drive", "MKR-02402419-77 Mockup Drive")
        self.assertFalse(passes(self.check(pages)))

    def test_wrong_lot_fails(self):
        self.assertFalse(passes(self.check(edited("lot 24, block 3", "lot 42, block 3"))))

    def test_wrong_house_number_fails(self):
        self.assertFalse(passes(self.check(edited("77 Mockup Drive, lot", "79 Mockup Drive, lot"))))

    def test_pos_naming_two_jobs_fail(self):
        spec = dict(self.SPEC, job_names=["MKR-02402401-77 Mockup Drive", "MKR-02402419-19 Other Way"])
        self.assertFalse(passes(self.check(request_pages(), spec)))

    def test_no_header_spec_checks_pages_only(self):
        self.assertTrue(passes(verify.check_pages(request_pages())))


if __name__ == "__main__":
    unittest.main()
