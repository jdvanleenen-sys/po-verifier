"""Loop run 5, 2026-11-09 (attack a07 on a real house): the POs read table's tax was edited to twice
what the PO prints and the request was numbered at 10%. Nothing checked the POs read table against
the PO file. Run from the repo root: python -m unittest discover -s tests"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import po_totals  # noqa: E402

PO = ("<html><body><table><tr><td>ORDER #: A-100/065</td></tr>"
      "<tr><td>Subtotal:</td><td>$4513.70</td></tr><tr><td>GST/HST Tax Total:</td><td>$0.00</td></tr>"
      "<tr><td>PST Tax Total:</td><td>$225.69</td></tr><tr><td>Total:</td><td>$4739.39</td></tr>"
      "</table></body></html>")
HEAD = ("## POs read\n| PO number | Subtotal | Tax lines | Total |\n|---|---|---|---|\n")


def read_back(sub="$4513.70", taxes="GST/HST $0.00; PST $225.69", total="$4739.39", po="A-100/065"):
    return HEAD + f"| {po} | {sub} | {taxes} | {total} |\n"


class POsReadAgainstThePO(unittest.TestCase):
    def run_check(self, text, files=(("PO A-100-065.html", PO),)):
        with tempfile.TemporaryDirectory() as d:
            for name, body in files:
                (Path(d) / name).write_text(body, encoding="utf-8")
            return po_totals.check(Path(d), text)

    def test_matching_row_passes(self):
        self.assertEqual(self.run_check(read_back()), ([], []))

    def test_tax_copied_wrong_is_refused(self):
        problems, _ = self.run_check(read_back(taxes="GST/HST $0.00; PST $451.37", total="$4965.07"))
        self.assertTrue(any("PST $225.69, the read-back says $451.37" in p for p in problems), problems)
        self.assertTrue(any("total $4739.39" in p for p in problems), problems)

    def test_subtotal_copied_wrong_is_refused(self):
        problems, _ = self.run_check(read_back(sub="$4531.70"))
        self.assertTrue(any("subtotal $4513.7" in p for p in problems), problems)

    def test_a_tax_the_po_does_not_print_is_refused(self):
        problems, _ = self.run_check(read_back(taxes="GST $225.69"))
        self.assertTrue(any("prints no GST tax" in p for p in problems), problems)
        self.assertTrue(any("leaves it out" in p for p in problems), problems)

    def test_a_zero_tax_may_be_left_out(self):
        self.assertEqual(self.run_check(read_back(taxes="PST $225.69")), ([], []))

    def test_a_po_number_no_file_prints_is_refused(self):
        problems, _ = self.run_check(read_back(po="A-10/065"))
        self.assertTrue(any("no PO in 01 intake prints this ORDER #" in p for p in problems), problems)

    def test_a_pdf_po_is_named_for_a_check_by_eye(self):
        problems, unchecked = self.run_check(read_back(po="B-7/001"), files=(("PO.pdf", "%PDF-1.4"),))
        self.assertEqual((problems, unchecked), ([], ["B-7/001"]))


if __name__ == "__main__":
    unittest.main()
