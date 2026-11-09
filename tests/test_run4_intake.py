"""Loop run 4, 2026-11-09: two gaps in what the gates hold onto across a house's read-backs.

1. A PO in 01 intake edited before a second read-back was fingerprinted afresh by grid-2, so the edit
   was never seen (a44): intake is now checked against the house's FIRST grid as well.
2. seal.py sealed a record that left a numbering gap below it; only the request caught it later (a28).

Run from the repo root: python -m unittest discover -s tests
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import intake_read  # noqa: E402
import seal  # noqa: E402


def house(d, po_text="PO 2 x $125.00 = $250.00"):
    intake = Path(d) / "01 intake" / "h"
    read = Path(d) / "02 read" / "h"
    intake.mkdir(parents=True)
    read.mkdir(parents=True)
    (intake / "po.html").write_text(po_text, encoding="utf-8")
    (read / "grid-1.md").write_text("# grid 1\n\n" + "\n".join(intake_read.section(intake)), encoding="utf-8")
    return intake, read


class IntakeAgainstTheFirstRead(unittest.TestCase):
    def test_a_po_edited_before_the_second_grid_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            intake, read = house(d)
            (intake / "po.html").write_text("PO 1 x $250.00 = $250.00", encoding="utf-8")
            (read / "grid-2.md").write_text("\n".join(intake_read.section(intake)), encoding="utf-8")
            found = intake_read.since_first_problems(intake, read, "h", below=2)
            self.assertEqual(len(found), 1, found)
            self.assertIn("po.html changed after the first read (grid-1.md)", found[0])

    def test_a_file_added_after_the_first_read_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            intake, read = house(d)
            (intake / "po copy.html").write_text("PO 2 x $125.00 = $250.00 ", encoding="utf-8")
            found = intake_read.since_first_problems(intake, read, "h", below=2)
            self.assertTrue(any("po copy.html was added after the first read" in f for f in found), found)

    def test_a_file_removed_after_the_first_read_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            intake, read = house(d)
            (intake / "po.html").unlink()
            found = intake_read.since_first_problems(intake, read, "h", below=2)
            self.assertTrue(any("po.html was read in grid-1.md but is gone" in f for f in found), found)

    def test_unchanged_intake_passes(self):
        with tempfile.TemporaryDirectory() as d:
            intake, read = house(d)
            self.assertEqual(intake_read.since_first_problems(intake, read, "h", below=2), [])

    def test_the_first_grid_is_not_checked_against_itself(self):
        with tempfile.TemporaryDirectory() as d:
            intake, read = house(d)
            (intake / "po.html").write_text("changed", encoding="utf-8")
            self.assertEqual(intake_read.since_first_problems(intake, read, "h", below=1), [])


def record(answer="yes"):
    return ("---\nhouse: h\nattempt: 3\nstage: 04 review\nstatus: draft\nfrom: 03 compare/h/variance-1.md\n---\n"
            f"\n## Sam's yes\n- Answer: {answer}\n- Name: Sam\n- Date: 2026-11-09\n")


class NoSealOverAGap(unittest.TestCase):
    def test_a_record_with_a_gap_below_it_is_not_sealed(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "04 review" / "h"
            folder.mkdir(parents=True)
            (folder / "review-1.md").write_text(record(), encoding="utf-8")
            three = folder / "review-3.md"
            three.write_text(record(), encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                seal.seal_file(three)
            self.assertIn("review-2.md is missing below it", caught.exception.args[0][0])
            self.assertNotIn("sealed:", three.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
