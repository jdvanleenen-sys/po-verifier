"""The rule grid, proved on planted mistakes. Run from the repo root:

    python -m unittest discover -s tests -v

Uses only 77 Mockup Drive. Each planted mistake must be refused; the clean grid must pass.
"""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import grid  # noqa: E402
import grid_check  # noqa: E402
import grid_read  # noqa: E402
import grid_rules  # noqa: E402

HOUSE = ROOT / "02 read" / "77-mockup-drive"
READ_BACK = (HOUSE / "read-back-1.md").read_text(encoding="utf-8")
GRID = (HOUSE / "grid-1.md").read_text(encoding="utf-8")
SNAPSHOT = (HOUSE / "price-list-1.csv").read_bytes()


def planted(text, old, new):
    assert old in text, f"planted change not found: {old}"
    return text.replace(old, new, 1)


def problems(read_back=READ_BACK, grid_text=GRID, final=True):
    return grid_check.check_grid(read_back, grid_text, SNAPSHOT, final)[0]


class CleanGrid(unittest.TestCase):
    def test_77_grid_passes(self):
        self.assertEqual(problems(), [])

    def test_every_row_and_po_gets_every_rule(self):
        cells = grid_read.expected_cells(READ_BACK, SNAPSHOT)
        self.assertEqual([k for k, _ in cells["rows"]], [str(n) for n in range(1, 8)])
        self.assertEqual(len(cells["pos"]), 3)
        for _, row in cells["rows"]:
            self.assertEqual(list(row), list(grid_rules.ROW_RULES))

    def test_build_gives_the_same_code_cells(self):
        built = grid_read.render("77-mockup-drive", 1, READ_BACK, SNAPSHOT)
        self.assertIn("pass: 8305 + 420 + 836 + 270 = 9831", built)
        self.assertIn("at risk: qty 7, selection 1; both recorded", built)


class Refused(unittest.TestCase):
    def assertRefused(self, words, **kw):
        found = problems(**kw)
        self.assertTrue(any(words in p for p in found), found)

    def test_unanswered_cell(self):
        self.assertRefused("not answered", grid_text=planted(GRID, "pass: count 1 against PO qty 1", "?"))

    def test_blank_cell(self):
        self.assertRefused("not answered", grid_text=planted(GRID, "pass: 34 LF against PO qty 30", " "))

    def test_answer_without_evidence(self):
        self.assertRefused("after the colon", grid_text=planted(GRID, "pass: 34 LF against PO qty 30", "pass:"))

    def test_answer_outside_the_rule(self):
        self.assertRefused("must start with", grid_text=planted(GRID, "pass: 34 LF against PO qty 30", "fine: ok"))

    def test_code_cell_changed(self):
        self.assertRefused("code says", grid_text=planted(GRID, "pass: 7 x 60 = 420", "pass: 7 x 60 = 430"))

    def test_row_missing_from_grid(self):
        line = next(l for l in GRID.splitlines() if l.startswith("| 5 |"))
        self.assertRefused("has rows", grid_text=planted(GRID, line + "\n", ""))

    def test_row_missing_from_grid_is_named(self):
        line = next(l for l in GRID.splitlines() if l.startswith("| 5 |"))
        found = problems(grid_text=planted(GRID, line + "\n", ""))
        self.assertTrue(any("'5'" in p for p in found), found)

    def test_column_dropped(self):
        self.assertRefused("the columns are", grid_text=planted(GRID, "| line-notes | count |", "| line-notes |"))

    def test_extra_cell_in_a_row(self):
        self.assertRefused("cells, not", grid_text=planted(GRID, "| pass: 34 LF against PO qty 30 |",
                                                           "| pass: 34 LF against PO qty 30 | pass: extra |"))

    def test_read_back_row_changed_after_the_grid(self):
        self.assertRefused("changed after the grid", read_back=planted(READ_BACK, '"stringers 34 ft"; 34 ft',
                                                                       '"stringers 36 ft"; 36 ft'))

    def test_line_total_that_does_not_add_up(self):
        changed = planted(READ_BACK, "| 7 | $60.00 | $420.00 |", "| 7 | $60.00 | $430.00 |")
        found = problems(read_back=changed)
        self.assertTrue(any("line-math" in p and "is not" in p for p in found), found)

    def test_at_risk_row_not_under_at_risk(self):
        changed = planted(READ_BACK, "Quantity and selection disagree: rows 3, 4, 5 (and 1, 6)",
                          "Quantity and selection disagree: rows 3, 4 (and 1, 6)")
        self.assertRefused("row 5 is at risk", read_back=changed)

    def test_ask_sam_refused_at_the_end_but_counted_before(self):
        asked = planted(GRID, "pass: 'prime 1' is one flat-rate wall prime", "ask Sam: prime or primer?")
        self.assertTrue(any("still waiting on Sam" in p for p in problems(grid_text=asked)))
        found, asks = grid_check.check_grid(READ_BACK, asked, SNAPSHOT, final=False)
        self.assertEqual((found, asks), ([], 1))

    def test_fail_answer_stops(self):
        self.assertRefused("Stop and ask Sam", grid_text=planted(
            GRID, "pass: prints 77 Mockup Drive", "fail: prints 79 Mockup Drive"))

    def test_grid_without_fingerprint(self):
        self.assertRefused("sha256", grid_text=planted(GRID, "read-back tables sha256:", "tables:"))


class NotComparable(unittest.TestCase):
    def test_not_comparable_rows_are_read(self):
        marked = planted(GRID, "pass: count 1 against PO qty 1", "not comparable: a lump sum")
        self.assertEqual(grid_check.not_comparable_rows(marked), {"1"})
        self.assertEqual(problems(grid_text=marked), [])


class MeasuredQty(unittest.TestCase):
    def qty(self, text):
        return grid_rules.measured_qty({"sam measured (his words)": text})

    def test_number_after_his_quoted_words(self):
        self.assertEqual(self.qty('"8\' doors x12 (they added the basement ones)"; count 12; no colour'),
                         Decimal("12"))

    def test_second_part_without_quotes(self):
        self.assertEqual(self.qty("stringers; 34 ft; no colour given"), Decimal("34"))

    def test_nothing_measured(self):
        self.assertIsNone(self.qty(""))


class Build(unittest.TestCase):
    def test_approved_read_back_grid_is_never_rebuilt(self):
        with self.assertRaises(SystemExit) as stop:
            grid.build("77-mockup-drive", replace=True)
        self.assertIn("approved", str(stop.exception))

    def test_existing_grid_is_not_overwritten(self):
        with self.assertRaises(SystemExit) as stop:
            grid.build("77-mockup-drive")
        self.assertIn("exists", str(stop.exception))


if __name__ == "__main__":
    unittest.main()
