"""Loop run 5 attacks on gates, request text and advice, 2026-11-09. Run from the repo root:

    python -m unittest discover -s tests -v

a20/a21/a23: seal.py sealed records the next stage refused (from: naming a missing file, a wrong
             attempt:, a grid with an open "ask Sam" cell); each fix then used up a number.
a22: a record with no attempt: line passed seal, build and commit.
a31: a non-ISO date under Sam's yes switched off the prepared-date check.
a32: the request said "Site notes not attached." while the notes were attached; a plain --notes yes
     sent a notes page that also held another house.
a08: an approved read-back edited after the yes got the advice "delete the variance".
a34: build and grid.py gave opposite advice for a file added to intake after the read.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import chain  # noqa: E402
import house_checks  # noqa: E402
import intake_read  # noqa: E402
import proof_choice  # noqa: E402
import proof_line  # noqa: E402
import seal  # noqa: E402


def record(attempt="attempt: 1\n", origin="from: 01 intake/h\n", day="2026-11-09"):
    return (f"---\nhouse: h\n{attempt}status: draft\n{origin}---\n\n"
            f"## Sam's yes\n- Answer: yes\n- Name: Sam\n- Date: {day}\n")


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "01 intake" / "h").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, stage, name, text):
        path = self.dir / stage / "h" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def refused(self, path):
        with self.assertRaises(ValueError) as caught:
            seal.seal_file(path)
        return " ".join(caught.exception.args[0])


class SealChecksTheChainFirst(Folder):
    def test_no_attempt_line_is_refused(self):
        path = self.put("04 review", "review-1.md", record(attempt=""))
        self.assertIn("no attempt: line", self.refused(path))
        self.assertTrue(any("no attempt: line" in p for p in chain.chain_problems(path, record(attempt=""), self.dir)))

    def test_wrong_attempt_is_refused(self):
        self.assertIn("attempt: 5", self.refused(self.put("04 review", "review-1.md", record(attempt="attempt: 5\n"))))

    def test_from_naming_a_missing_file_is_refused(self):
        path = self.put("04 review", "review-1.md", record(origin="from: 03 compare/h/variance-2.md\n"))
        self.assertIn("variance-2.md", self.refused(path))
        self.assertNotIn("sealed", path.read_text(encoding="utf-8").split("---")[1])

    def test_a_good_record_still_seals(self):
        self.assertIn("sealed: review-1.md", seal.seal_file(self.put("04 review", "review-1.md", record())))


class SealRunsTheGridCheck(Folder):
    STUB = ("import sys\nprint('grid-1.md is refused:')\nprint('- row 8, count: still waiting on Sam')\n"
            "sys.exit({code})\n")

    def grid_script(self, code):
        script = self.dir / "02 read" / "grid.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(self.STUB.format(code=code), encoding="utf-8")

    def test_a_read_back_whose_grid_is_refused_is_not_sealed(self):
        self.grid_script(1)
        reason = self.refused(self.put("02 read", "read-back-1.md", record()))
        self.assertIn("fails the grid check", reason)
        self.assertIn("still waiting on Sam", reason)

    def test_a_read_back_whose_grid_passes_seals(self):
        self.grid_script(0)
        self.assertIn("sealed: read-back-1.md", seal.seal_file(self.put("02 read", "read-back-1.md", record())))

    def test_only_the_highest_read_back_is_sealed(self):
        self.grid_script(0)
        first = self.put("02 read", "read-back-1.md", record())
        self.put("02 read", "read-back-2.md", record(attempt="attempt: 2\n", origin="from: 02 read/h/read-back-1.md\n"))
        self.assertIn("not the highest read-back", self.refused(first))


class YesDate(unittest.TestCase):
    def test_a_non_iso_date_is_refused(self):
        problems = seal.yes_problems(record(day="Nov 9, 2026"))
        self.assertTrue(any("YYYY-MM-DD" in p for p in problems), problems)

    def test_an_iso_date_passes(self):
        self.assertEqual(seal.yes_problems(record()), [])


REQUEST = "VPO request ... Proof attached. PO A-1/065, {notes} How to read this. ..."


class ProofSentence(unittest.TestCase):
    def proof(self, attached, left_out):
        return {"po_numbers": [], "epo_names": [], "notes_attached": attached, "notes_left_out": left_out}

    def test_not_attached_while_attached_is_refused(self):
        found = proof_line.problems(REQUEST.format(notes="Site notes not attached."), self.proof(["notes.jpg"], []))
        self.assertTrue(found, found)

    def test_attached_and_named_passes(self):
        text = REQUEST.format(notes="and the site notes (notes.jpg).")
        self.assertEqual(proof_line.problems(text, self.proof(["notes.jpg"], [])), [])

    def test_left_out_must_say_not_attached(self):
        text = REQUEST.format(notes="and the site notes.")
        self.assertTrue(proof_line.problems(text, self.proof([], ["notes.jpg"])))
        text = REQUEST.format(notes="Site notes not attached.")
        self.assertEqual(proof_line.problems(text, self.proof([], ["notes.jpg"])), [])

    def test_some_pages_attached_must_be_named(self):
        text = REQUEST.format(notes="and the site notes of October 2, 2026.")
        self.assertTrue(proof_line.problems(text, self.proof(["a.jpg"], ["b.jpg"])))

    def test_a_house_with_no_notes_needs_no_sentence(self):
        self.assertEqual(proof_line.problems("VPO request", self.proof([], [])), [])


class OtherHouseNotes(unittest.TestCase):
    def test_a_shared_page_needs_the_explicit_answer(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "house-info.md").write_text("- Address: 12 Sample Road\nIt covers two houses.\n",
                                                  encoding="utf-8")
            shared = proof_choice.other_house(d)
        self.assertTrue(shared)
        notes = [Path("notes.jpg")]
        with self.assertRaises(SystemExit):
            proof_choice.choose_notes(notes, "yes", shared)
        self.assertEqual(proof_choice.choose_notes(notes, "yes-other-house", shared), notes)
        self.assertEqual(proof_choice.choose_notes(notes, "no", shared), [])

    def test_a_page_for_this_house_only_takes_plain_yes(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "house-info.md").write_text("- Address: 12 Sample Road\n", encoding="utf-8")
            self.assertFalse(proof_choice.other_house(d))


class Advice(unittest.TestCase):
    def test_an_edited_approved_read_back_is_undone_not_the_variance_deleted(self):
        with tempfile.TemporaryDirectory() as d:
            shown, advice = house_checks.stop_message(d, "h", [
                "the read-back was changed after Sam's yes. Approved files never change",
                "variance row 'railing' (A-1/065): measured qty 26 is not Sam's size as read back (16)"])
        self.assertIn("undo the edit", advice)
        self.assertNotIn("Delete the variance", advice)

    def test_one_message_for_a_file_added_to_intake(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "intake"
            folder.mkdir()
            (folder / "po.html").write_text("x", encoding="utf-8")
            grid = intake_read.HEADING + "\n\n| File | sha256 |\n|---|---|\n"
            later = intake_read.problems(folder, grid, "h")
        self.assertEqual(len(later), 1)
        self.assertIn("starts a new house folder, h-2", later[0])
        self.assertIn("starts a new house folder", intake_read.added("h", "po.html", "the first read (grid-1.md)"))


if __name__ == "__main__":
    unittest.main()
