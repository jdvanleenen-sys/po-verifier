"""Loop run 6 on a real house, 2026-11-09: Sam's words read wrong, and price-list twins let through.
Run from the repo root: python -m unittest discover -s tests -v

1. a01/a03: curly quotes (from a phone or Word) switched off every check on his quoted words, and
   prime marks (16′6″) were not read as feet and inches.
2. a02/a04: "2x Railing 16'", "16' + 8'", "*2", "(2 sides)" read as 16.
3. "Sam confirmed" anywhere in the cell let any slot pass; now only "Sam confirmed <the slot's number>".
4. a05/a07: twins differing by an inner space or punctuation ("Hand rail", "(Builder X.)") passed.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "02 read")]
import grid_rules as rules  # noqa: E402
import prices  # noqa: E402


def row(said):
    return {"#": "9", "po number": "A-1/065", "po qty": "15", "unit price": "40.00", "line total": "600.00",
            "price list item": "Railing", "sam measured (his words)": said}


def size(said):
    found = rules.measured_qty(row(said))
    return None if found is None else str(found)


class CurlyQuotesAndPrimes(unittest.TestCase):
    def test_curly_quotes_still_check_his_words(self):
        self.assertIsNone(size("\u201cRailing 16\u2019\u201d; 61 ft; photo line 1"))

    def test_curly_quotes_still_read_a_good_size(self):
        self.assertEqual(size("\u201cRailing 16\u2019\u201d; 16 ft; photo line 1"), "16")

    def test_prime_marks_are_feet_and_inches(self):
        self.assertIsNone(size("\"Railing 16\u20326\u2033\"; 16 ft"))


class JoinsAndMultipliers(unittest.TestCase):
    def test_each_reads_as_no_size(self):
        for said in ("\"2x Railing 16'\"; 16 ft", "\"Railing 16' + 8'\"; 16 ft", "\"Railing 16' *2\"; 16 ft",
                     "\"Railing 16' (2 sides)\"; 16 ft", "\"Railing 16' & 8'\"; 16 ft"):
            with self.subTest(said=said):
                self.assertIsNone(size(said))

    def test_a_count_written_x12_still_reads(self):
        self.assertEqual(size("\"8' doors x12\"; count 12"), "12")


class SamConfirmedNamesItsNumber(unittest.TestCase):
    def test_bare_sam_confirmed_no_longer_lets_any_slot_pass(self):
        self.assertIsNone(size("\"Railing 16'\"; 61 ft, Sam confirmed"))

    def test_confirmed_number_lets_that_slot_pass(self):
        self.assertEqual(size("\"3.016 sf\"; 3016, Sam confirmed 3016"), "3016")

    def test_confirmed_number_must_be_the_slot(self):
        self.assertIsNone(size("\"Railing 16'\"; 61 ft, Sam confirmed 16"))


class PriceTwins(unittest.TestCase):
    def test_inner_space_and_punctuation_are_twins(self):
        self.assertEqual(prices.alike("Hand rail"), prices.alike("Handrail"))
        self.assertEqual(prices.alike("Railing, wood (Builder X.)"), prices.alike("Railing - wood (Builder X)"))

    def test_different_items_stay_different(self):
        self.assertNotEqual(prices.alike("Bench detail (lid)"), prices.alike("Bench detail (no lid)"))


if __name__ == "__main__":
    unittest.main()
