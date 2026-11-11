"""Findings from an outside tester (2026-11-07), each proved fixed. Run from the repo root:

    python -m unittest discover -s tests -v
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import printing  # noqa: E402
import verify  # noqa: E402

SAMPLE = ROOT / "05 request" / "77-mockup-drive" / "vpo-request-1.pdf"
PYTHON3_LINE = "On a Mac or Linux, type `python3` wherever these files say `python`."


class MacPython(unittest.TestCase):
    """A stock Mac has only python3; the rule files say python. The map says so near the top."""

    def test_root_context_says_python3_near_the_top(self):
        head = (ROOT / "CONTEXT.md").read_text(encoding="utf-8").splitlines()[:10]
        self.assertIn(PYTHON3_LINE, "\n".join(head))

    def test_readme_says_python3(self):
        self.assertIn(PYTHON3_LINE, (ROOT / "README.md").read_text(encoding="utf-8"))



def passes(result):
    return ": pass:" in result


class PageLine(unittest.TestCase):
    """The request page printed "page 1 of 1" in a file of 6 pages. It now says which pages are the
    request, how many are proof, and how many the file holds, from the real counts."""

    def setUp(self):
        self.request, self.proof = verify.split_request(verify.pdf_pages(SAMPLE))

    def printed(self, wording):
        return [self.request[0].replace("page 1 of 1", wording, 1)] + self.request[1:]

    def test_wording_names_request_proof_and_file_pages(self):
        self.assertEqual(printing.page_words(1, 5), "Request page 1 of 1. Proof attached: 5 pages (6 pages in this file).")
        self.assertEqual(printing.page_words(2, 1), "Request page 1 of 2. Proof attached: 1 page (3 pages in this file).")

    def test_layout_carries_the_new_mark(self):
        layout = (ROOT / "reference" / "request-layout.html").read_text(encoding="utf-8")
        self.assertIn(printing.PAGE_MARK, layout)
        self.assertNotIn("page 1 of {{PAGES}}", layout)

    def test_a_draft_with_the_old_page_line_is_refused_before_printing(self):
        draft = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, draft, True)
        (draft / "request.html").write_text("<p>VR-0001, page 1 of {{PAGES}}</p>", encoding="utf-8")
        with self.assertRaises(SystemExit) as stop:
            printing.print_request("no-browser", draft, 5)
        self.assertIn("Copy the layout again", str(stop.exception))

    def test_right_counts_pass_check_6(self):
        n = len(self.proof)
        result = verify.check_pages(self.printed(printing.page_words(1, n)), proof_pages=n)
        self.assertTrue(passes(result), result)

    def test_wrong_proof_count_fails_check_6(self):
        n = len(self.proof)
        result = verify.check_pages(self.printed(printing.page_words(1, n + 1)), proof_pages=n)
        self.assertFalse(passes(result), result)
        self.assertIn("proof", result)

    def test_wrong_file_count_fails_check_6(self):
        n = len(self.proof)
        wording = printing.page_words(1, n).replace(f"({n + 1} pages", f"({n + 2} pages")
        result = verify.check_pages(self.printed(wording), proof_pages=n)
        self.assertFalse(passes(result), result)


if __name__ == "__main__":
    unittest.main()
