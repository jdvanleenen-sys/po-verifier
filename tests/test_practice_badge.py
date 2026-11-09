"""Loop run 3, 2026-11-09: a real contractor's request printed the layout's "PRACTICE SAMPLE. MADE-UP
DATA." badge and passed every check. Run from the repo root: python -m unittest discover -s tests"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import contractor  # noqa: E402
import header_checks  # noqa: E402

PAGE = "PRACTICE SAMPLE. MADE-UP DATA. VPO request JOB 12 Sample Road BUILDER X before tax"


def badge(header):
    return [p for p in header_checks.header_problems([PAGE], header) if "practice sample" in p.lower()]


class PracticeBadge(unittest.TestCase):
    def base(self, practice):
        return {"contractor": "", "builders": "", "practice": practice, "document": "VR-0001",
                "job_numbers": None, "job_names": ["x"], "measured": None}

    def test_real_contractor_refuses_the_badge(self):
        self.assertEqual(len(badge(self.base(False))), 1)

    def test_practice_folder_keeps_the_badge(self):
        self.assertEqual(badge(self.base(True)), [])

    def test_repo_stand_in_reads_as_practice(self):
        self.assertTrue(contractor.read(ROOT / "reference" / "contractor.md")["practice"])

    def test_a_real_setup_reads_as_real(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "contractor.md"
            f.write_text("| Business, and who signs | Real Co. (vendor V00123) |\n", encoding="utf-8")
            self.assertFalse(contractor.read(f)["practice"])


if __name__ == "__main__":
    unittest.main()
