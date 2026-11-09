"""Loop run 2 attacks on approvals, 2026-11-09. Run from the repo root:

    python -m unittest discover -s tests -v

a03  an approved review was edited, its seal line deleted and seal.py run again: it sealed.
a42  the grid's Intake read table was edited after Sam's yes on the read-back: nothing noticed.
a38  a review decision "on hold (...)" counted as on.
a45/a47  a record saved as Windows-1252 gave a garbled message or a traceback.
msg  the "records do not agree" advice named numbers that already existed and a variance by hand.
mtime  commit refused a copied folder because file times moved, though no byte changed.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import house_checks  # noqa: E402
import records  # noqa: E402
import seal  # noqa: E402

RECORD = """---
house: 12-sample-road
attempt: 1
status: draft
---

# 12-sample-road, review 1

| Row | Item | Sam's decision (on / off) |
|---|---|---|
| 3 | Handrail | off |

## Sam's yes
- Answer: yes, to the table exactly as shown
- Name: Sam
- Date: 2026-11-09
"""


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8", newline="\n")
        return path


class SealedOnce(Folder):
    def test_edited_and_resealed_is_refused(self):
        path = self.write("review-1.md", RECORD)
        seal.seal_file(path)
        text = path.read_text(encoding="utf-8").replace("| off |", "| on |")
        path.write_text(seal.unsealed(text), encoding="utf-8")
        with self.assertRaises(ValueError) as caught:
            seal.seal_file(path)
        self.assertIn("sealed before", caught.exception.args[0][0])

    def test_a_sealed_file_passes_the_ledger(self):
        path = self.write("review-1.md", RECORD)
        seal.seal_file(path)
        self.assertEqual(seal.file_approval_problems(path), [])

    def test_sealed_outside_seal_py_is_refused(self):
        path = self.write("review-1.md", seal.seal_text("review-1.md", RECORD))
        problems = seal.file_approval_problems(path)
        self.assertTrue(problems and "no line of seals.md" in problems[0], problems)

    def test_ledger_hash_must_match(self):
        path = self.write("review-1.md", RECORD)
        seal.seal_file(path)
        other = seal.seal_text("review-1.md", RECORD.replace("| off |", "| on |"))
        path.write_text(other, encoding="utf-8", newline="\n")
        self.assertIn(seal.CHANGED, seal.file_approval_problems(path))


class GridSealedWithReadBack(Folder):
    def test_grid_changed_after_the_yes_is_refused(self):
        grid = self.write("grid-1.md", "| file | sha256 |\n| a.html | 1111 |\n")
        path = self.write("read-back-1.md", RECORD.replace("review 1", "read-back 1"))
        seal.seal_file(path)
        self.assertEqual(seal.file_approval_problems(path), [])
        grid.write_text("| file | sha256 |\n| a.html | 2222 |\n", encoding="utf-8")
        problems = seal.file_approval_problems(path)
        self.assertTrue(problems and "grid-1.md changed after Sam's yes" in problems[0], problems)


class Decisions(unittest.TestCase):
    def test_only_on_or_off_count(self):
        for cell, want in [("on", "on"), ("ON", "on"), ("off", "off"), ("off (Sam: leave the doors off)", "off"),
                           ("on (Sam: chase it)", "on"), ("on hold (ask the super first)", None),
                           ("only if the super agrees", None), ("maybe", None), ("", None), ("offset", None)]:
            with self.subTest(cell=cell):
                self.assertEqual(records.decision_word(cell), want)

    def test_refusal_words(self):
        self.assertIn("blank is not a decision", records.decision_problem(""))
        self.assertIn("'on hold' is not on or off", records.decision_problem("on hold"))


class Encoding(Folder):
    def test_windows_1252_is_refused_in_words(self):
        path = self.dir / "review-1.md"
        path.write_bytes(RECORD.replace("Sam's yes", "Sam’s yes").encode("cp1252"))
        with self.assertRaises(SystemExit) as caught:
            records.read_text(path)
        self.assertEqual(str(caught.exception), "review-1.md is not saved as UTF-8. Save it as UTF-8 and run again.")

    def test_seal_py_refuses_it_in_words(self):
        path = self.dir / "review-1.md"
        path.write_bytes(RECORD.replace("Sam's yes", "Sam’s yes").encode("cp1252"))
        with self.assertRaises(SystemExit) as caught:
            seal.main(["seal.py", str(path)])
        self.assertIn("not saved as UTF-8", str(caught.exception))


class FixAdvice(Folder):
    def test_names_the_real_next_numbers(self):
        for stage, names in (("02 read", ("read-back-1.md", "read-back-2.md")), ("04 review", ("review-1.md",))):
            (self.dir / stage / "h").mkdir(parents=True)
            for n in names:
                (self.dir / stage / "h" / n).write_text("x", encoding="utf-8")
        advice = house_checks.fix_advice(self.dir, "h")
        self.assertIn("read-back-3.md", advice)
        self.assertIn("review-2.md", advice)
        self.assertNotIn("variance-2", advice)


class HtmlByContent(Folder):
    def test_file_time_alone_does_not_refuse(self):
        html = self.write("request.html", "<p>request</p>")
        checks = f"html sha256: {house_checks.sha256(html)}\n"
        os.utime(html, (1, 4_000_000_000))
        self.assertIsNone(house_checks.html_problem(html, checks))

    def test_changed_bytes_refuse(self):
        html = self.write("request.html", "<p>request</p>")
        checks = f"html sha256: {house_checks.sha256(html)}\n"
        html.write_text("<p>request, edited</p>", encoding="utf-8")
        self.assertIn("changed after the last build", house_checks.html_problem(html, checks))

    def test_no_recorded_hash_refuses(self):
        html = self.write("request.html", "<p>request</p>")
        self.assertIn("Build again", house_checks.html_problem(html, "pdf sha256: x\n"))


if __name__ == "__main__":
    unittest.main()
