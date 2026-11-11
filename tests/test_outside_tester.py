"""Findings from an outside tester (2026-11-07), each proved fixed. Run from the repo root:

    python -m unittest discover -s tests -v
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON3_LINE = "On a Mac or Linux, type `python3` wherever these files say `python`."


class MacPython(unittest.TestCase):
    """A stock Mac has only python3; the rule files say python. The map says so near the top."""

    def test_root_context_says_python3_near_the_top(self):
        head = (ROOT / "CONTEXT.md").read_text(encoding="utf-8").splitlines()[:10]
        self.assertIn(PYTHON3_LINE, "\n".join(head))

    def test_readme_says_python3(self):
        self.assertIn(PYTHON3_LINE, (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
