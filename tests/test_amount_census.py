"""No amount on the request that the records do not give; no PO counted as attached from its EPO's page.

    python -m unittest discover -s tests -v

Found by the 2026-11-05 test loop: a wrong per-PO total in the main box's note, an invented amount in
a why, a row printed without its sign, and a missing PO whose number sat on its EPO's page all passed.
"""
import copy
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
sys.path.insert(0, str(ROOT / "tests"))
import verify  # noqa: E402
import test_row_binding  # noqa: E402

CommittedSamplePdf = test_row_binding.CommittedSamplePdf

PDF = CommittedSamplePdf.PDF
ROW_END = "PO quantity short of the site count."


def passes(result):
    return ": pass:" in result


def sample():
    text = " ".join(verify.split_request(verify.pdf_pages(PDF))[0])
    exp = copy.deepcopy(CommittedSamplePdf.EXP)
    exp["house"] = {"before": D("972.00"), "tax": D("48.60"), "total": D("1020.60")}
    exp["other_amounts"] = [D("60.00"), D("25.00"), D("50.00")]
    return " ".join(text.split()), exp


class NoAmountTheRecordsDoNotGive(unittest.TestCase):
    def test_sample_passes(self):
        text, exp = sample()
        for check in (verify.check_rows, verify.check_house):
            self.assertTrue(passes(check(text, exp)), check(text, exp))

    def test_wrong_per_po_total_in_the_box_note_fails(self):
        text, exp = sample()
        wrong = text.replace("PO MKR-02402401/027: $315.00", "PO MKR-02402401/027: $999.00", 1)
        self.assertNotEqual(wrong, text)
        self.assertFalse(passes(verify.check_house(wrong, exp)))

    def test_box_note_totals_swapped_fails(self):
        """Both amounts are real figures, so only binding each to its own PO catches the swap."""
        text, exp = sample()
        wrong = text.replace("PO MKR-02402401/027: $315.00. No PO: $705.60",
                             "PO MKR-02402401/027: $705.60. No PO: $315.00", 1)
        self.assertNotEqual(wrong, text)
        self.assertFalse(passes(verify.check_house(wrong, exp)))

    def test_invented_amount_in_a_why_fails(self):
        text, exp = sample()
        wrong = text.replace(ROW_END, ROW_END + " Builder owes $5,000.00.", 1)
        self.assertFalse(passes(verify.check_rows(wrong, exp)))

    def test_row_printed_without_a_sign_fails(self):
        text, exp = sample()
        extra = "Paint garage door EA $60.00 0 $60.00 $0.00 1 $60.00 $500.00 Asked on site."
        self.assertFalse(passes(verify.check_rows(text.replace(ROW_END, ROW_END + " " + extra, 1), exp)))

    def test_an_epo_amount_named_in_a_why_passes(self):
        text, exp = sample()
        exp["other_amounts"].append(D("210.00"))
        ok = text.replace(ROW_END, ROW_END + " Amount includes EPO 01, $210.00.", 1)
        self.assertTrue(passes(verify.check_rows(ok, exp)), verify.check_rows(ok, exp))


PO_PAGE = "Purchase Order Request ORDER #: MKR-02402440/{n} COST CODE: PAIN-010"
EPO_PAGE = "Extra Purchase Order EPO NAME V00999 - MKR-02402440/027 - EPO 01 EPO TOTAL $210.00"
NOTES_PAGE = "site-notes.txt 40 Larch railing PO MKR-02402440/027 short"
PROOF = {"po_numbers": ["MKR-02402440/012", "MKR-02402440/027"], "epo_names": ["V00999 - MKR-02402440/027 - EPO 01"],
         "notes_attached": ["site-notes.txt"], "notes_left_out": []}


class PoProof(unittest.TestCase):
    def test_every_po_on_its_own_page_passes(self):
        pages = [PO_PAGE.format(n="012"), PO_PAGE.format(n="027"), EPO_PAGE, NOTES_PAGE]
        self.assertTrue(passes(verify.check_proof(pages, PROOF)), verify.check_proof(pages, PROOF))

    def test_po_found_only_on_its_epo_page_fails(self):
        pages = [PO_PAGE.format(n="012"), EPO_PAGE]
        result = verify.check_proof(pages, dict(PROOF, notes_attached=[]))
        self.assertFalse(passes(result))
        self.assertIn("MKR-02402440/027", result)

    def test_po_found_only_on_the_notes_page_fails(self):
        pages = [PO_PAGE.format(n="012"), EPO_PAGE, NOTES_PAGE]
        self.assertFalse(passes(verify.check_proof(pages, PROOF)))


if __name__ == "__main__":
    unittest.main()
