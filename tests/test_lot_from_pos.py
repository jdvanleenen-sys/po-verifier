"""Loop run 2, 2026-11-09: a house whose drop-in note gives no lot could not print the lot on the
request, though every PO printed it, so Sam was asked a question his POs answered. Run from the
repo root: python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import house_checks  # noqa: E402


class LotFromPOs(unittest.TestCase):
    def test_every_po_agrees(self):
        texts = ["LOT/BLOCK/UNIT: 22/6/ PLAN", "LOT/BLOCK/UNIT: 22/6/ X", "LOT/BLOCK 22/6 TRADE"]
        self.assertEqual(house_checks.lot_from_pos(texts), ["22", "6"])

    def test_pos_disagree_gives_none(self):
        self.assertIsNone(house_checks.lot_from_pos(["LOT/BLOCK/UNIT: 22/6/", "LOT/BLOCK/UNIT: 23/6/"]))

    def test_no_lot_printed_gives_none(self):
        self.assertIsNone(house_checks.lot_from_pos(["JOB NAME: X JOB ADDRESS: Y"]))


if __name__ == "__main__":
    unittest.main()
