"""Builders write POs their own way. Run from the repo root:

    python -m unittest discover -s tests -v

Found by a peer test on 2026-11-05: a second builder's PO (number SRH-2026-0417, no slash; the
same item on several numbered lines) was refused by the money gate, because the gate knew one
builder's PO number shape and named a row by PO and item. PO numbers now come from the read-back's
own "POs read" table, and a row is named by its read-back row number. These tests use the shapes
real builder systems print (see tests/po-styles/README.md).
"""
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import header_checks  # noqa: E402
import money  # noqa: E402
import verify  # noqa: E402
from request_text import NO_HEADING, group_blocks  # noqa: E402

PO = "SRH-2026-0417"
SHAPES = {PO, "OP 4471203", "KBH/2026/0091 Rev 02", "5521", "SC-2214-007", "PO-0317", "MKR-02402401/027"}

READ_BACK = f"""## POs read
| PO number | Subtotal | Tax lines | Total |
|---|---|---|---|
| {PO} | $1568.80 | HST (13%) $203.94 | $1772.74 |

## EPOs read
none in the folder

## Rows
| # | PO number | Line as printed | Unit as printed | PO qty | Unit price | Line total | Special option info | Sam measured | Price list item | Unit | Rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | {PO} | 1.01 Living Room Walls | SF | 480 | $1.85 | $888.00 | none printed | "480"; 480 | Walls | SF | 1.85 |
| 2 | {PO} | 3.01 Bedroom Walls | SF | 368 | $1.85 | $680.80 | none printed | "392"; 392 | Walls | SF | 1.85 |
"""

VARIANCE_ROWS = [
    ("1", "| 1 | SRH-2026-0417 | Walls | SF | $1.85 | 480 | $1.85 | $888.00 | 480 | $888.00 | $0.00 | matches | matches |"),
    ("2", "| 2 | SRH-2026-0417 | Walls | SF | $1.85 | 368 | $1.85 | $680.80 | 392 | $725.20 | +$44.40 | PO quantity short | flag |"),
]


def variance(with_row=True):
    head = "| Row | PO number | Item | Unit | Agreed rate | PO qty | PO rate | PO amount | Measured qty | Measured value | Variance | Why | Call |"
    rows = [r for _, r in VARIANCE_ROWS]
    if not with_row:
        head = head.replace("| Row ", "", 1)
        rows = ["|" + r.split("|", 2)[2] for r in rows]
    return "## Rows\n" + head + "\n|---|\n" + "\n".join(rows) + "\n"


def review(with_row=True):
    head = "| Row | PO number | Item | Variance | Call | Sam's decision (on / off) | Reason |"
    rows = ["| 1 | SRH-2026-0417 | Walls | $0.00 | matches | off (not chosen) | |",
            "| 2 | SRH-2026-0417 | Walls | +$44.40 | flag | on | |"]
    if not with_row:
        head = head.replace("| Row ", "", 1)
        rows = ["|" + r.split("|", 2)[2] for r in rows]
    return head + "\n|---|\n" + "\n".join(rows) + "\n"


class PoNumbersInAnyShape(unittest.TestCase):
    def test_each_shape_is_read_as_written(self):
        for shape in SHAPES:
            self.assertEqual(money.po_key(f"  {shape} ", SHAPES), shape)

    def test_a_cell_naming_a_po_with_other_words_finds_it(self):
        self.assertEqual(money.po_key("SC-2214-007 (change order CCO-003)", SHAPES), "SC-2214-007")

    def test_no_po_is_none(self):
        for cell in ("none", "None", ""):
            self.assertEqual(money.po_key(cell, SHAPES), money.NO_PO)

    def test_read_back_rows_and_tax_rate_use_the_pos_read_number(self):
        rows, rates, _ = money.read_back(READ_BACK)
        self.assertEqual({r["po"] for r in rows}, {PO})
        self.assertEqual(rates[PO], D("203.94") / D("1568.80"))


class OneItemOnSeveralLines(unittest.TestCase):
    def rows(self):
        return money.read_back(READ_BACK)[0]

    def test_each_variance_row_matches_its_own_read_back_row(self):
        problems = []
        found = money.variance_rows(variance(), self.rows(), [], problems)
        self.assertEqual(problems, [])
        self.assertEqual(sorted(found), [(PO, "walls", "1"), (PO, "walls", "2")])
        self.assertEqual(found[(PO, "walls", "2")]["difference"], D("44.40"))

    def test_without_a_row_column_the_repeated_item_is_refused(self):
        problems = []
        money.variance_rows(variance(with_row=False), self.rows(), [], problems)
        self.assertTrue(any("matches 2 read-back rows" in p for p in problems), problems)

    def test_review_rows_are_matched_by_row_number(self):
        problems = []
        found = money.variance_rows(variance(), self.rows(), [], problems)
        chosen = money.decisions(review(), found, problems)
        self.assertEqual(problems, [])
        self.assertEqual(chosen, {(PO, "walls", "1"): False, (PO, "walls", "2"): True})

    def test_review_without_row_numbers_is_refused(self):
        problems = []
        found = money.variance_rows(variance(), self.rows(), [], problems)
        money.decisions(review(with_row=False), found, problems)
        self.assertTrue(any("could be any of read-back rows 1, 2" in p for p in problems), problems)

    def test_repeated_item_prints_with_its_po_line(self):
        rows = [("walls", "1", {}), ("walls", "2", {}), ("doors", "3", {})]
        lines = {"1": "1.01 Living Room Walls", "2": "3.01 Bedroom Walls", "3": "5.01 Doors"}
        self.assertEqual(money.row_label("walls", "2", rows, lines), "walls, PO line 3.01")
        self.assertEqual(money.row_label("doors", "3", rows, lines), "doors")
        self.assertEqual(money.row_label("walls", "1", rows, {"1": "Living room walls"}), "walls, Living room walls")


HEADINGS = "ITEM\nUNIT\nAGREED RATE\nPO QTY\nPO RATE\nPO AMOUNT\nMEASURED QTY\nMEASURED VALUE\nDIFFERENCE\nWHY\n"


def wall_row(label, po_qty, po_amount, qty, value, diff):
    expected = {"po": PO, "item": "walls", "label": label, "rate": D("1.85"), "po_qty": D(po_qty),
                "po_amount": D(po_amount), "measured_qty": D(qty), "measured_value": D(value), "difference": D(diff)}
    cells = [label, "SF", "$1.85", po_qty, "$1.85", f"${po_amount}", qty, f"${value}", f"+${diff}", "Short."]
    return expected, cells


ROWS = [wall_row("Walls, PO line 1.01", "480", "888.00", "500", "925.00", "37.00"),
        wall_row("Walls, PO line 3.01", "368", "680.80", "392", "725.20", "44.40")]


def request(rows, po=PO):
    body = "".join("\n".join(cells) + "\n" for _, cells in rows)
    return (f"PO {po} Interior paint.\n" + HEADINGS + body + "Difference before tax\n+$81.40\n"
            "HST 13%, from this PO's own tax line\n$10.58\nEPO requested for this PO\n$91.98\n")


def expected(rows):
    return {"rows_on": [e for e, _ in rows], "po_numbers": [PO]}


class RequestForAnyBuilder(unittest.TestCase):
    def test_heading_with_spaces_in_the_po_number_is_its_group(self):
        text = "PO OP 4471203 Interior paint.\nDifference before tax\n$0.00\nEPO requested for this PO\n$0.00\n"
        self.assertEqual(list(group_blocks(text, ["OP 4471203"])[0]), ["op 4471203"])

    def test_group_under_a_po_the_records_do_not_give_is_refused(self):
        text = request(ROWS).replace(f"PO {PO}", "PO SRH-2026-9999")
        self.assertIn(": fail:", verify.check_differences(text, expected(ROWS)))

    def test_group_with_no_po_heading_is_not_skipped(self):
        text = request(ROWS) + "Extra work.\nDifference before tax\n+$50.00\nEPO requested for this PO\n$52.50\n"
        self.assertIn(NO_HEADING, group_blocks(text, [PO])[0])
        self.assertIn(": fail:", verify.check_differences(text, expected(ROWS)))

    def test_same_item_on_two_po_lines_reads_each_row(self):
        result = verify.check_differences(request(ROWS), expected(ROWS))
        self.assertIn(": pass:", result, result)

    def test_same_item_rows_with_figures_swapped_fail(self):
        swapped =[(ROWS[0][0], [ROWS[0][1][0]] + ROWS[1][1][1:]), (ROWS[1][0], [ROWS[1][1][0]] + ROWS[0][1][1:])]
        self.assertIn(": fail:", verify.check_differences(request(swapped), expected(ROWS)))


class JobLineNeedsSomethingToCheck(unittest.TestCase):
    def test_no_job_name_and_no_house_info_is_refused(self):
        spec = {"document": "VR-0001", "job_numbers": None, "job_names": []}
        problems = header_checks.header_problems(["Job 27 Birchwood Crescent builder VR-0001 before tax"], spec)
        self.assertTrue(any("nothing to check the job line against" in p for p in problems), problems)

    def test_no_job_name_but_house_info_numbers_still_checks_them(self):
        spec = {"document": "VR-0001", "job_numbers": ["27", "14"], "job_names": []}
        page = "Job 27 Birchwood Crescent, lot 14 builder VR-0001 before tax"
        self.assertEqual(header_checks.header_problems([page], spec), [])
        self.assertTrue(header_checks.header_problems([page.replace("lot 14", "lot 41")], spec))


if __name__ == "__main__":
    unittest.main()
