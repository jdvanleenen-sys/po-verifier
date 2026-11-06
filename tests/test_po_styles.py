"""Twelve builders' PO styles, each run through stages 02 to 05 by the stages' own code. Run from
the repo root:

    python -m unittest discover -s tests -v

Every builder prints a PO its own way (tests/po-styles/README.md lists each style and what it
imitates). For each style the records a correct run writes are built from tests/po-styles/styles.json
(pipeline.py), and:
- the money gate must pass them and work out the request the answer key gives, or refuse with the
  reason the key gives;
- a request laid out the way the PDF reads must pass checks 1 to 4;
- one planted mistake at a time, on that style's own request, must fail.
The answer key is worked out in pipeline.py without any stage code, each tax rounded on its own.
"""
import json
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests" / "po-styles"))
import pipeline  # noqa: E402  (puts 02 read, 03 compare and 05 request on the path)
import money  # noqa: E402
import verify  # noqa: E402

STYLES = json.loads((ROOT / "tests" / "po-styles" / "styles.json").read_text(encoding="utf-8"))["styles"]
CHECKS = (verify.check_rows, verify.check_differences, verify.check_tax, verify.check_house)


def gate(style):
    records, problems = pipeline.records(style)
    expected, more = money.expected_request(records)
    return expected, problems + more


def failures(text, expected):
    return [r for r in (c(text, expected) for c in CHECKS) if ": fail:" in r]


def requested(style):
    return [s for s in STYLES if s["expect"] == "request"] if style is None else [style]


class EachStyleThroughTheGate(unittest.TestCase):
    def test_gate_works_out_the_answer_key(self):
        for style in requested(None):
            with self.subTest(style["slug"]):
                expected, problems = gate(style)
                self.assertEqual(problems, [])
                got = {po: (g["before"], g["tax"], g["total"]) for po, g in expected["groups"].items()}
                self.assertEqual(got, pipeline.answer_key(style))

    def test_refused_styles_are_refused_for_the_right_reason(self):
        for style in [s for s in STYLES if s["expect"].startswith("refused")]:
            with self.subTest(style["slug"]):
                _, problems = gate(style)
                reason = style["expect"].split(":", 1)[1].strip()
                self.assertTrue(any(reason in p for p in problems), problems)

    def test_request_laid_out_right_passes_checks_1_to_4(self):
        for style in requested(None):
            with self.subTest(style["slug"]):
                expected, _ = gate(style)
                self.assertEqual(failures(pipeline.request_text(style, expected), expected), [])


class PlantedMistakesOnEachStyle(unittest.TestCase):
    def planted(self, change):
        """Each style's own request with one change; the change returns None where it does not apply."""
        for style in requested(None):
            expected, _ = gate(style)
            text = change(pipeline.request_text(style, expected), expected)
            if text is None:
                continue
            with self.subTest(style["slug"]):
                self.assertTrue(failures(text, expected), "the planted mistake passed")

    def test_a_row_difference_changed_fails(self):
        def change(text, exp):
            d = exp["rows_on"][0]["difference"]
            return text.replace(pipeline.money(d, True), pipeline.money(d + D("100"), True), 1)
        self.planted(change)

    def test_a_group_total_changed_fails(self):
        def change(text, exp):
            g = next(iter(exp["groups"].values()))
            return text.replace("\n" + pipeline.money(g["total"]) + "\n", "\n" + pipeline.money(g["total"] + D("1")) + "\n", 1)
        self.planted(change)

    def test_a_group_under_part_of_its_po_number_fails(self):
        def change(text, exp):
            po = next((p for p in exp["groups"] if p != "none"), "")
            return text.replace(f"PO {po} Interior", f"PO {po[:-2]} Interior", 1) if len(po) > 3 else None
        self.planted(change)

    def test_a_tax_rate_changed_on_the_group_line_fails(self):
        def change(text, exp):
            return text.replace("%, from this PO's own tax line", "1%, from this PO's own tax line", 1)
        self.planted(change)

    def test_a_repeated_item_printed_without_its_po_line_fails(self):
        def change(text, exp):
            labelled = [r for r in exp["rows_on"] if r["label"] != r["item"]]
            return text.replace(labelled[0]["label"] + "\n", labelled[0]["item"] + "\n", 1) if labelled else None
        self.planted(change)


class RecordsChangedAfterSamSaidYes(unittest.TestCase):
    def test_a_variance_figure_changed_is_refused(self):
        for style in requested(None):
            with self.subTest(style["slug"]):
                records, _ = pipeline.records(style)
                row = next(l for l in records["variance"].splitlines() if l.startswith(f"| {style['on'][0]} |"))
                cells = row.split("|")
                cells[9] = f" {cells[9].strip()}1 "
                records["variance"] = records["variance"].replace(row, "|".join(cells), 1)
                _, problems = money.expected_request(records)
                self.assertTrue(problems)


if __name__ == "__main__":
    unittest.main()
