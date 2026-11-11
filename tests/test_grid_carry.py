"""Rebuilding a draft read-back's grid never loses an answer. Run from the repo root:

    python -m unittest discover -s tests -v

An outside tester (2026-11-07) rebuilt a grid with --replace and every '?' he had answered was
wiped. Now each answer whose row is unchanged is carried into the new grid, and each answer that
cannot be carried (its row changed) is named in the message so it is asked again.
"""
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import grid  # noqa: E402
import grid_check  # noqa: E402
import grid_read  # noqa: E402

HOUSE = "zz-grid-carry-test"
SOURCE = ROOT / "02 read" / "77-mockup-drive"
FOLDER = ROOT / "02 read" / HOUSE
ANSWERED = (SOURCE / "grid-1.md").read_text(encoding="utf-8")
STRINGERS, STRINGERS_CHANGED = '"stringers 34 ft"; 34 ft', '"stringers 36 ft"; 36 ft'


def answers_of(grid_text):
    found = {}
    for heading in ("row grid", "po grid"):
        header, rows = grid_read.table(grid_read.under(grid_text, heading))
        found.update({(r[0], h): c for r in rows for h, c in zip(header[1:], r[1:])})
    return found


def answer(grid_text, source=ANSWERED):
    """Answer every '?' as the finished 77 Mockup Drive grid answered it."""
    known, lines, header = answers_of(source), [], []
    for line in grid_text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| ") and cells[0] in ("#", "PO number"):
            header = cells
        elif line.startswith("| ") and "?" in cells:
            cells = [known.get((cells[0], header[i]), c) if c == "?" else c for i, c in enumerate(cells)]
            line = "| " + " | ".join(cells) + " |"
        lines.append(line)
    return "\n".join(lines) + "\n"


class ReplaceKeepsAnswers(unittest.TestCase):
    def setUp(self):
        self.tearDown()
        shutil.copytree(ROOT / "01 intake" / "77-mockup-drive", ROOT / "01 intake" / HOUSE)
        FOLDER.mkdir(parents=True)
        shutil.copyfile(SOURCE / "price-list-1.csv", FOLDER / "price-list-1.csv")
        self.read_back = (SOURCE / "read-back-1.md").read_text(encoding="utf-8").replace(
            "status: approved", "status: draft", 1)
        self.write("read-back-1.md", self.read_back)
        grid.build(HOUSE)
        self.write("grid-1.md", answer(self.grid()))

    def tearDown(self):
        shutil.rmtree(ROOT / "01 intake" / HOUSE, ignore_errors=True)
        shutil.rmtree(FOLDER, ignore_errors=True)

    def write(self, name, text):
        (FOLDER / name).write_text(text, encoding="utf-8")

    def grid(self):
        return (FOLDER / "grid-1.md").read_text(encoding="utf-8")

    def problems(self, read_back):
        snapshot = (FOLDER / "price-list-1.csv").read_bytes()
        return grid_check.check_grid(read_back, self.grid(), snapshot, final=True)[0]

    def test_answered_cells_survive_a_replace(self):
        before = answers_of(self.grid())
        message = grid.build(HOUSE, replace=True)
        self.assertEqual(answers_of(self.grid()), before)
        self.assertEqual(self.problems(self.read_back), [])
        self.assertIn("carried", message)
        self.assertIn("0 cell(s) are '?'", message)

    def test_a_changed_row_is_reported_not_kept_or_dropped(self):
        old_count = answers_of(self.grid())[("5", "count")]
        self.write("read-back-1.md", self.read_back.replace(STRINGERS, STRINGERS_CHANGED, 1))
        message = grid.build(HOUSE, replace=True)
        now = answers_of(self.grid())
        self.assertEqual(now[("5", "count")], "?")
        self.assertEqual(now[("5", "note-match")], "?")
        self.assertIn("row 5, count", message)
        self.assertIn(old_count, message)
        self.assertEqual(now[("4", "count")], answers_of(ANSWERED)[("4", "count")])
        self.assertNotIn("row 4,", message)

    def test_a_grid_with_no_row_fingerprints_reports_every_answer(self):
        self.write("grid-1.md", ANSWERED.replace("status: approved", "status: draft"))
        message = grid.build(HOUSE, replace=True)
        self.assertNotIn("pass:", "".join(c for (_, h), c in answers_of(self.grid()).items()
                                          if h in ("note-match", "count")))
        self.assertIn("row 1, count", message)
        self.assertIn("PO MKR-02402401/012, address", message)


if __name__ == "__main__":
    unittest.main()
