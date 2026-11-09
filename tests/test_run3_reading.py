"""Loop run 3 on a real house, 2026-11-09: what the attacker got past the reading. Made-up data only.
Run from the repo root: python -m unittest discover -s tests -v

a09/a10/a11  a multiplier in Sam's words or the slot's remark ("10' x2", "two of them", "each side")
             read as one size
a28          a price row whose name hides a zero-width space sat beside the real row at another rate
a46          a row's PO qty and line total read off another line of the PO passed every check
a50          prices.py check on a read-back saved as Windows-1252 stopped with a traceback
"""
import shutil
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "02 read")]
import grid_rules as rules  # noqa: E402
import po_lines  # noqa: E402
import prices  # noqa: E402

HOUSE = ROOT / "tests" / "houses" / "40-larch-crescent" / "intake"
PO = "MKR-02402440/027"


def row(said):
    return {"#": "2", "po number": "A-1/094", "po qty": "16", "unit price": "40.00", "line total": "640.00",
            "price list item": "Railing", "sam measured (his words)": said}


class MultipliersAskSam(unittest.TestCase):
    def test_a_multiplier_anywhere_is_not_one_size(self):
        for said in ("\"Fireplace mantel 10' x2\"; 10 ft; no colour", "\"Shelves 124' ×2\"; 124 ft",
                     "\"Mantel 10'\"; 10 ft, two of them", "\"Railing 13'\"; 13 ft each side",
                     "\"Railing 13' each side\"; 13 ft", "\"Railing 13'\"; 13 each side",
                     "\"Railing 13'\"; 13 ft, both sides", "\"Mantel 10'\"; 10 ft, a pair",
                     "\"Mantel 10'\"; 10 ft, double", "\"Mantel 10'\"; 10 ft, twice",
                     "\"Mantel 10'\"; 10 ft, plus 4 more", "\"Mantel 10'\"; 10 ft, three of those",
                     "\"Doors 6 each\"; 6"):
            with self.subTest(said=said):
                self.assertIsNone(rules.measured_qty(row(said)))

    def test_counts_sources_and_remarks_still_read(self):
        for said, want in (("\"8' doors x12 (they added the basement ones)\"; count 12; no colour", "12"),
                           ("\"8' doors 12\"; 0 here, counted on /027", "0"),
                           ("\"done as ordered\"; 2152; Sam confirmed", "2152"),
                           ("\"GARAGE incl ceiling, 420 sf. said a change order was coming, never saw one.\"; "
                            "420 sf; no colour given", "420"),
                           ("\"Handrail 14'\"; 14 ft; no colour given (photo, under \"12 Sample Road\", line 2)", "14"),
                           ("\"doors\"; 3 each", "3")):
            with self.subTest(said=said):
                self.assertEqual(rules.measured_qty(row(said)), Decimal(want))


def price_list(*rows):
    return ("Item,Unit,Rate,Active\n" + "".join(f"{r},LF,{rate},TRUE\n" for r, rate in rows)).encode("utf-8")


class InvisibleCharactersInNames(unittest.TestCase):
    def test_zero_width_space_is_refused_by_row(self):
        for ch in ("​", "‌", "‍", "﻿", " ", "⁠"):
            with self.subTest(ch=hex(ord(ch))):
                _, problems = prices.parse(price_list(("Handrail", "8.25"), (f"Hand{ch}rail", "9.25")))
                self.assertTrue(any("line 3" in p and "invisible" in p for p in problems), problems)

    def test_dash_twins_name_both_lines(self):
        _, problems = prices.parse(price_list(("Railing — wood", "40"), ("Rail", "5"), ("Railing - wood", "45")))
        twin = [p for p in problems if "differ only" in p]
        self.assertEqual(len(twin), 1, problems)
        self.assertIn("lines 2 and 4", twin[0])

    def test_alike_strips_invisible_characters(self):
        self.assertEqual(prices.alike("Hand​rail"), prices.alike("Handrail"))


def read_back(*rows):
    head = ("## Rows\n| # | PO number | Line as printed | Unit as printed | PO qty | Unit price | Line total |\n"
            "|---|---|---|---|---|---|---|\n")
    return head + "".join(f"| {n} | {po} | {line} | LF | {q} | {p} | {t} |\n" for n, po, line, q, p, t in rows)


class PoLineIsOnThePO(unittest.TestCase):
    def test_rows_read_off_their_own_lines_pass(self):
        text = read_back(("1", PO, "(5120) 09900/020S - Interior Railing - Wood", "20", "$38.00", "$760.00"),
                         ("2", PO, "09900/030S - 8' Doors & Trim", "12", "$60.00", "$720.00"))
        self.assertEqual(po_lines.check(HOUSE, text), ([], 0))

    def test_numbers_from_another_line_fail(self):
        text = read_back(("1", PO, "(5120) 09900/020S - Interior Railing - Wood", "12", "$60.00", "$720.00"))
        problems, _ = po_lines.check(HOUSE, text)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("20 x 38 = 760", problems[0])
        self.assertIn("not 12 x 60 = 720", problems[0])

    def test_a_line_the_po_does_not_print_fails(self):
        text = read_back(("1", PO, "09900/099S - Ceiling Fans", "1", "$10.00", "$10.00"))
        problems, _ = po_lines.check(HOUSE, text)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("prints no line", problems[0])

    def test_a_pdf_po_is_counted_not_passed(self):
        folder = ROOT / "tests" / "po-styles" / "12-quarry-lane" / "intake"
        text = read_back(("1", "CRH-03311807/014", "anything", "1", "$1.00", "$1.00"))
        self.assertEqual(po_lines.check(folder, text), ([], 1))


class AnsiReadBackInPlainWords(unittest.TestCase):
    HOUSE = "zz-run3-ansi-test"

    def tearDown(self):
        shutil.rmtree(ROOT / "02 read" / self.HOUSE, ignore_errors=True)

    def test_prices_check_names_the_encoding(self):
        folder = ROOT / "02 read" / self.HOUSE
        folder.mkdir(parents=True)
        (folder / "read-back-1.md").write_bytes("# read-back — café\n".encode("cp1252"))
        with self.assertRaises(SystemExit) as stop:
            prices.main(["prices.py", "check", self.HOUSE])
        self.assertIn("not saved as UTF-8", str(stop.exception))


if __name__ == "__main__":
    unittest.main()
