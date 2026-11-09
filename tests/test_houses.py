"""The six test houses, checked against themselves. Run from the repo root:

    python -m unittest discover -s tests -v

For each house in tests/houses/houses.json this re-reads the generated POs and EPOs, prices every
row from reference/price-list.xlsx, applies the thresholds in reference/contractor.md, and checks
the expected variance total, house flag and request totals. A wrong answer key fails here before
it can mislead a test run. No browser needed.
"""
import html
import json
import re
import sys
import unittest
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOUSES = ROOT / "tests" / "houses"
sys.path.insert(0, str(ROOT / "02 read"))
import prices  # noqa: E402
sys.path.insert(0, str(HOUSES))
import make_houses  # noqa: E402

SPEC = json.loads((HOUSES / "houses.json").read_text(encoding="utf-8"))["houses"]
PRICE_LIST = prices.parse(prices.source_bytes())[0]
CENT = Decimal("0.01")


def thresholds():
    """Ignore line and flag line, from the one home for them."""
    text = (ROOT / "reference" / "contractor.md").read_text(encoding="utf-8")
    ignore = re.search(r"Ignore line \| under \$(\d+)", text)
    flag = re.search(r"Flag line \| \$(\d+) and up", text)
    return Decimal(ignore.group(1)), Decimal(flag.group(1))


IGNORE, FLAG = thresholds()


def call(variance):
    size = abs(variance)
    if size == 0:
        return "matches"
    if size < IGNORE:
        return "ignore"
    return "flag" if size >= FLAG else "sam's call"


def plain(path):
    """A PO or EPO file as plain text, one cell per line."""
    text = re.sub(r"<[^>]+>", "\n", path.read_text(encoding="utf-8"))
    return [c for c in (html.unescape(x).replace("\xa0", " ").strip() for x in text.splitlines()) if c]


def printed(cells, label):
    index = cells.index(label)
    return Decimal(cells[index + 1].replace("$", "").replace(",", ""))


def po_lines(cells):
    """(description, uom, qty, unit price, total) for each line printed on a PO."""
    found = []
    for i, cell in enumerate(cells):
        if cell == "(5120)":
            desc, uom, qty, price, total = cells[i + 1:i + 6]
            found.append((desc.rstrip(" :"), uom, Decimal(qty), Decimal(price.strip("$")), Decimal(total.strip("$"))))
    return found


def row_amounts(row):
    """PO amount, measured value and variance for one expected row, priced from the list."""
    if row.get("unpriced"):
        return None
    rate = PRICE_LIST[row["item"].lower()]["rate"]
    po_amount = Decimal(row.get("po_qty", "0")) * Decimal(row.get("po_rate", "0")) + Decimal(row.get("epo", "0"))
    measured = Decimal(row["measured"]) * rate
    return po_amount, measured, measured - po_amount


class House(unittest.TestCase):
    def check_pos(self, h):
        folder = HOUSES / h["slug"] / "intake"
        rates = {}
        for po in h["pos"]:
            cells = plain(folder / f"PO {po['number'].replace('/', '-')}.html")
            self.assertIn(po["number"], cells)
            self.assertIn(h["address"], " ".join(cells))
            lines = po_lines(cells)
            self.assertEqual(len(lines), len(po["lines"]), po["number"])
            for desc, uom, qty, price, total in lines:
                self.assertEqual(qty * price, total, f"{po['number']} {desc}")
            subtotal, tax = printed(cells, "Subtotal:"), printed(cells, "GST/HST Tax Total:")
            self.assertEqual(sum(t for *_, t in lines), subtotal, po["number"])
            self.assertEqual(subtotal + tax, printed(cells, "Total:"), po["number"])
            rates[po["number"]] = tax / subtotal
        return rates

    def check_rows(self, h):
        notes = make_houses.notes_text(h).replace(",", "")
        variances = {}
        for row in h["rows"]:
            self.assertIn(row["measured"], notes, f"{h['slug']}: measured {row['measured']} is not in the notes")
            if row.get("unpriced"):
                continue
            match = PRICE_LIST.get(row["item"].lower())
            self.assertTrue(match and match["active"], f"{h['slug']}: '{row['item']}' is not an active price row")
            variances[(row["po"], row["item"])] = row_amounts(row)[2]
        return variances

    def check_request(self, h, rates, variances):
        on = [tuple(k) for k in h["expected"]["on"]]
        for key in on:
            self.assertIn(key, variances, f"{h['slug']}: on-row {key} is not a priced row")
        if h["expected"]["request"] is None:
            self.assertEqual(on, [], h["slug"])
            return
        before = tax = Decimal(0)
        for po in {k[0] for k in on}:
            group = sum(variances[k] for k in on if k[0] == po)
            rate = rates[po] if po != "none" else set(rates.values()).pop()
            before += group
            tax += (group * rate).quantize(CENT, ROUND_HALF_UP)
        want = h["expected"]["request"]
        self.assertEqual((before, tax, before + tax),
                         (Decimal(want["before"]), Decimal(want["tax"]), Decimal(want["total"])), h["slug"])

    def test_every_house_adds_up(self):
        for h in SPEC:
            with self.subTest(house=h["slug"]):
                rates = self.check_pos(h)
                self.assertEqual(len(set(rates.values())), 1, "every PO in a test house carries the same GST rate")
                variances = self.check_rows(h)
                total = sum(variances.values(), Decimal(0))
                self.assertEqual(total, Decimal(h["expected"]["total"]))
                self.assertEqual(abs(total) >= FLAG, h["expected"]["house_flagged"])
                self.check_request(h, rates, variances)

    def test_flagged_rows_are_on_unless_sam_said_off(self):
        """Every flagged row is either on, or named in Sam's review answer as taken off or left off."""
        for h in SPEC:
            review = " ".join(a for when, a in h["sam_answers"] if when.startswith("At review")).lower()
            on = [tuple(k) for k in h["expected"]["on"]]
            for row in h["rows"]:
                amounts = row_amounts(row)
                if amounts and call(amounts[2]) == "flag" and (row["po"], row["item"]) not in on:
                    with self.subTest(house=h["slug"], row=row["item"]):
                        self.assertTrue("off" in review, f"flagged row left off without Sam saying so: {review}")


if __name__ == "__main__":
    unittest.main()
