"""Loop run 3 attacks on approvals and gates, 2026-11-09. Run from the repo root:

    python -m unittest discover -s tests -v

a16/a17: "Yes, but take the lockers off.", "Yes?" and "yes-ish" were sealed as Sam's yes.
a05: an approved review edited, its seal and ledger line deleted, and sealed again, after a request
     was already built from it.
a25: "I don't know, ask Joe" passed as Sam's answer to a not-on-the-price-list warning.
a20: a record with its from: line deleted passed compare.
a49: a request check saved as ANSI stopped commit with a traceback.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import chain  # noqa: E402
import grid_check  # noqa: E402
import house_checks  # noqa: E402
import seal  # noqa: E402


def record(answer):
    return (f"---\nhouse: h\nattempt: 1\nstage: 04 review\nstatus: draft\nfrom: 01 intake/h\n---\n\n"
            f"## Sam's yes\n- Answer: {answer}\n- Name: Sam\n- Date: 2026-11-09\n")


def house(d):
    """The intake folder every record() names in its from: line (seal.py checks it since loop run 5)."""
    (Path(d) / "01 intake" / "h").mkdir(parents=True, exist_ok=True)


class PlainYesOnly(unittest.TestCase):
    def test_conditions_and_questions_are_refused(self):
        for said in ("Yes?", "Yes, but take the lockers (row 7) off.", "Yes and no. I don't know about row 7.",
                     "yes-ish, check with Joe first", "Yesterday", "No", "I don't know"):
            with self.subTest(said=said):
                problems = seal.yes_problems(record(said))
                self.assertTrue(problems and "not a plain yes" in problems[0], problems)

    def test_the_plain_forms_are_a_yes(self):
        for said in ("yes", "Yes.", "yes, to the whole table", "Yes, to the table with those decisions.",
                     "yes, to the table exactly as shown"):
            with self.subTest(said=said):
                self.assertEqual(seal.yes_problems(record(said)), [])


class NoSealAfterUse(unittest.TestCase):
    def test_a_review_a_request_was_built_from_is_not_sealed_again(self):
        with tempfile.TemporaryDirectory() as d:
            house(d)
            review = Path(d) / "04 review" / "h" / "review-1.md"
            check = Path(d) / "05 request" / "h" / "request-check-1.md"
            review.parent.mkdir(parents=True)
            check.parent.mkdir(parents=True)
            review.write_text(record("yes, to the table exactly as shown"), encoding="utf-8")
            check.write_text("from review: 04 review/h/review-1.md\n", encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                seal.seal_file(review)
            self.assertIn("already used by request-check-1.md", caught.exception.args[0][0])

    def test_a_read_back_is_not_used_by_its_own_grid(self):
        # Loop run 4, 2026-11-09: grid-N.md names its read-back in from:, and the used-record rule
        # counted it, so no new read-back could ever be sealed.
        with tempfile.TemporaryDirectory() as d:
            house(d)
            rb = Path(d) / "02 read" / "h" / "read-back-1.md"
            rb.parent.mkdir(parents=True)
            rb.write_text(record("yes, to the whole table"), encoding="utf-8")
            (rb.parent / "grid-1.md").write_text("from: 02 read/h/read-back-1.md\n", encoding="utf-8")
            self.assertIn("sealed: read-back-1.md", seal.seal_file(rb))

    def test_another_read_backs_grid_still_counts_as_a_use(self):
        with tempfile.TemporaryDirectory() as d:
            house(d)
            rb = Path(d) / "02 read" / "h" / "read-back-1.md"
            rb.parent.mkdir(parents=True)
            rb.write_text(record("yes"), encoding="utf-8")
            (rb.parent / "read-back-2.md").write_text("from: 02 read/h/read-back-1.md\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                seal.seal_file(rb)

    def test_an_unused_record_still_seals(self):
        with tempfile.TemporaryDirectory() as d:
            house(d)
            review = Path(d) / "04 review" / "h" / "review-1.md"
            review.parent.mkdir(parents=True)
            review.write_text(record("yes"), encoding="utf-8")
            self.assertIn("sealed: review-1.md", seal.seal_file(review))


WARNING = """
## WARNING: not on the price list (1 items)
| PO number | Description as printed | Qty and unit | Closest items | Sam's answer (add row / names item / leave unpriced) |
|---|---|---|---|---|
| A-1/093 | Wall Prime | 1 EA | none | {answer} |

## Rows
| # | PO number | Price list item |
|---|---|---|
| 1 | A-1/093 | not on the price list |
"""


class WarningAnswers(unittest.TestCase):
    def test_a_non_answer_is_refused(self):
        problems = grid_check.warning_problems(WARNING.format(answer="I don't know, ask Joe"))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("no answer from Sam", problems[0])

    def test_the_three_answers_pass(self):
        for answer in ("leave unpriced: payment split", "add row: Wall prime, EA, $1000", "names item: Wall prime"):
            with self.subTest(answer=answer):
                self.assertEqual(grid_check.warning_problems(WARNING.format(answer=answer)), [])


class FromLineRequired(unittest.TestCase):
    def test_a_record_without_from_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            house(d)
            path = Path(d) / "02 read" / "h" / "read-back-1.md"
            path.parent.mkdir(parents=True)
            text = "---\nhouse: h\nattempt: 1\nstatus: draft\n---\n"
            path.write_text(text, encoding="utf-8")
            problems = chain.chain_problems(path, text, Path(d))
            self.assertTrue(any("has no from: line" in p for p in problems), problems)


class AnsiRequestCheck(unittest.TestCase):
    def test_plain_words_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            house(d)
            check = Path(d) / "request-check-1.md"
            check.write_bytes("from review: 04 review/h/review-1.md\n- Name: Sam B\xe9land —\n".encode("cp1252"))
            with self.assertRaises(SystemExit) as caught:
                house_checks.review_used(d, "04 review/h/review-1.md")
            self.assertIn("not saved as UTF-8", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
