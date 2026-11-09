"""The price list check, proved on planted mistakes. Run from the repo root:

    python -m unittest discover -s tests -v

Each planted mistake in the price list file or in the read-back's prices must be refused, by
prices.py on its own and by the money gate before a request is numbered. Uses only 77 Mockup
Drive and made-up price files.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import money  # noqa: E402
import prices  # noqa: E402  (money puts 02 read on the path)
from test_money_gate import regrid, texts  # noqa: E402

GOOD = b"Item,Unit,Rate,Active\nHandrail,LF,10,TRUE\n\"Railing, wood\",LF,38,TRUE\n"


def file_problems(raw):
    return prices.parse(raw)[1]


class PriceFile(unittest.TestCase):
    """The file Sam saves from Excel."""

    def assertRefused(self, raw, words):
        problems = file_problems(raw)
        self.assertTrue(any(words in p for p in problems), problems)

    def test_clean_file_reads(self):
        rows, problems = prices.parse(GOOD)
        self.assertEqual(problems, [])
        self.assertEqual(str(rows["railing, wood"]["rate"]), "38")

    def test_the_real_price_list_reads_clean(self):
        rows, problems = prices.parse(prices.source_bytes())
        self.assertEqual(problems, [])
        self.assertEqual(sum(r["active"] for r in rows.values()), 52)

    def test_excel_bom_crlf_and_dollar_signs_are_read(self):
        raw = b"\xef\xbb\xbfItem,Unit,Rate,Active\r\nWall prime,EA,\"$1,000.00\",TRUE\r\n"
        rows, problems = prices.parse(raw)
        self.assertEqual(problems, [])
        self.assertEqual(rows["wall prime"]["rate"], prices.to_rate("1000"))

    def test_semicolon_file_is_refused_with_how_to_fix(self):
        self.assertRefused(b"Item;Unit;Rate;Active\nHandrail;LF;10;TRUE\n", "semicolons")

    def test_rate_that_is_not_a_number_is_refused(self):
        self.assertRefused(GOOD.replace(b",10,", b",ten,"), "is not a number")

    def test_unknown_unit_is_refused(self):
        self.assertRefused(GOOD.replace(b"Handrail,LF", b"Handrail,FT"), "unit 'FT'")

    def test_same_item_active_twice_is_refused(self):
        self.assertRefused(GOOD + b"Handrail,LF,12,TRUE\n", "twice as active")

    def test_missing_column_is_refused(self):
        self.assertRefused(GOOD + b"Stubwall,LF,8\n", "3 columns")

    def test_wrong_header_is_refused(self):
        self.assertRefused(b"Name,Unit,Price,Active\nHandrail,LF,10,TRUE\n", "first line")


class ReadBackPrices(unittest.TestCase):
    """The rates written into Sam's read-back, against the frozen snapshot it names."""

    def assertGateRefuses(self, words, **changes):
        _, problems = money.expected_request(texts(**changes))
        self.assertTrue(any(words in p for p in problems), problems)

    def test_clean_read_back_matches_its_snapshot(self):
        records = texts()
        self.assertEqual(prices.check_read_back(records["read-back"], records["price-list"]), [])

    def test_rate_changed_in_read_back_is_refused(self):
        self.assertGateRefuses("the price list says 38",
                               **{"read-back": ("| Railing, wood | LF | 38 |", "| Railing, wood | LF | 35 |")})

    def test_nearest_item_instead_of_listed_one_is_refused(self):
        self.assertGateRefuses("not on the price list snapshot",
                               **{"read-back": ("| Railing, wood | LF | 38 |", "| Railing | LF | 38 |")})

    def test_wrong_unit_is_refused(self):
        self.assertGateRefuses("unit 'SF'", **{"read-back": ("| Floor SF | 2.75 |", "| SF | 2.75 |")})

    def test_snapshot_edited_after_the_read_is_refused(self):
        self.assertGateRefuses("has changed since",
                               **{"price-list": (b"Railing, wood\",LF,38", b"Railing, wood\",LF,48")})

    def test_missing_snapshot_is_refused(self):
        records = texts()
        records["price-list"] = None
        _, problems = money.expected_request(records)
        self.assertTrue(any("is not in the house's 02 read folder" in p for p in problems), problems)

    def test_read_back_naming_no_snapshot_is_refused(self):
        self.assertGateRefuses("does not name a price-list-N.csv",
                               **{"read-back": ("price-list-1.csv", "reference/price-list.csv")})

    def test_pick_one_row_passes_at_read_but_never_at_the_gate(self):
        records = texts(**{"read-back": ("| Railing, wood | LF | 38 |", "| pick one (Sam to choose) | | |")})
        self.assertEqual(prices.check_read_back(records["read-back"], records["price-list"], pending_ok=True), [])
        _, problems = money.expected_request(records)
        self.assertTrue(any("waiting on Sam's pick" in p for p in problems), problems)

    def test_row_sam_left_unpriced_needs_no_variance_row(self):
        row = ('| 8 | none | (on no PO) | | | | | | "soffits"; 60 ft '
               '| not on the price list (Sam: leave unpriced) | | |')
        garage = "| Prime and paint garage, including ceiling | SF | 1.6 |"
        extra = "## Extra items (in Sam's notes, on no PO)\n"
        records = texts()
        records["read-back"] = (records["read-back"].replace(garage, f"{garage}\n{row}", 1)
                                .replace(extra, f"{extra}- Row 8: soffits, 60 ft, left unpriced by Sam.\n", 1))
        records["grid"] = regrid(records["read-back"], records["grid"], records["price-list"])
        self.assertIn(row, records["read-back"])
        self.assertIn("Row 8: soffits", records["read-back"])
        exp, problems = money.expected_request(records)
        self.assertEqual(problems, [])
        self.assertEqual(str(exp["house"]["total"]), "1020.60")

    def test_unpriced_row_with_dollars_in_the_variance_is_refused(self):
        row = "| none | not on the price list | | | | | $0.00 | 2 | | -$210.00 | unpriced | |"
        self.assertGateRefuses("belongs in the 'Not comparable",
                               variance=("| missing from every PO | flag |", f"| missing from every PO | flag |\n{row}"))

    def test_inactive_item_is_refused(self):
        raw = texts()["price-list"].replace(b"\"Railing, wood\",LF,38,TRUE", b"\"Railing, wood\",LF,38,FALSE")
        records = texts()
        records["read-back"] = records["read-back"].replace(prices.fingerprint(records["price-list"]),
                                                            prices.fingerprint(raw))
        records["price-list"] = raw
        _, problems = money.expected_request(records)
        self.assertTrue(any("is not active" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
