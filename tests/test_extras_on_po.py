"""Work on no PO can go on a PO's EPO, when Sam names that PO in the review. Run from the repo root:

    python -m unittest discover -s tests -v

Jeff, 2026-11-08: a builder's main PO carries the whole list of work, so extras found on site go on
that PO's one EPO, each still on its own line so the builder can track it. The review's
"EPO goes on" column says which PO. Left blank, an extra stays in its own "No PO" group, as before.
"""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_money_gate import money, texts, verify  # noqa: E402

OLD_HEAD = "| Reason, if a flagged row is taken off |\n|---|---|---|---|---|---|\n"
NEW_HEAD = "| Reason, if a flagged row is taken off | EPO goes on |\n|---|---|---|---|---|---|---|\n"
DOORS = "| on (flagged rows go on unless Sam takes one off) | |\n| MKR-02402401/027 | Stringer"
STRINGER = "| off (not chosen) | |\n| none"
GARAGE = "| none | Prime and paint garage, including ceiling | +$672.00 | flag | on (flagged rows go on unless Sam takes one off) | |"


def review_with(garage_target, doors_target=""):
    """77's review with the 'EPO goes on' column, the garage row naming garage_target."""
    review = texts()["review"]
    for old, new in ((OLD_HEAD, NEW_HEAD),
                     (DOORS, DOORS.replace("| |\n", f"| | {doors_target} |\n")),
                     (STRINGER, "| off (not chosen) | | |\n| none"),
                     (GARAGE, GARAGE + f" {garage_target} |")):
        assert old in review, old
        review = review.replace(old, new, 1)
    return review


def expected(review):
    records = texts()
    records["review"] = review
    return money.expected_request(records)


class ExtrasOnAPo(unittest.TestCase):
    def test_extra_named_on_a_po_joins_that_po_group(self):
        out, problems = expected(review_with("MKR-02402401/027"))
        self.assertEqual(problems, [])
        self.assertEqual(list(out["groups"]), ["MKR-02402401/027"])
        self.assertEqual(out["groups"]["MKR-02402401/027"]["before"], Decimal("972.00"))
        garage = [r for r in out["rows_on"] if r["row"] == "7"][0]
        self.assertEqual(garage["po"], "MKR-02402401/027")
        self.assertFalse(garage["on_po"])

    def test_house_total_is_unchanged_by_the_move(self):
        moved, _ = expected(review_with("MKR-02402401/027"))
        plain, _ = money.expected_request(texts())
        self.assertEqual(moved["house"]["before"], plain["house"]["before"])

    def test_blank_column_keeps_the_no_po_group(self):
        out, problems = expected(review_with(""))
        self.assertEqual(problems, [])
        self.assertIn("none", out["groups"])

    def test_a_po_not_in_the_house_is_refused(self):
        _, problems = expected(review_with("MKR-99999999/001"))
        self.assertTrue(any("is not a PO in this house" in p for p in problems), problems)

    def test_a_row_on_one_po_cannot_move_to_another(self):
        _, problems = expected(review_with("", doors_target="MKR-02402401/041"))
        self.assertTrue(any("is on PO MKR-02402401/027" in p for p in problems), problems)

    def test_item_count_still_counts_the_extra_as_on_no_po(self):
        out, _ = expected(review_with("MKR-02402401/027"))
        box = "before tax $972.00 2 items: 1 on a po, 1 on no po tax total requested"
        self.assertEqual(verify.box_text_problems(box, out), [])


if __name__ == "__main__":
    unittest.main()
