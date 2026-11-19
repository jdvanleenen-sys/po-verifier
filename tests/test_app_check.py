"""The phone app's runner, step 3: the Check screen. Open questions become cards, Sam's answers go
to the agent for the next read-back, and his yes is written and sealed by the folder's own seal.py.
Runs on 77 Mockup Drive with its read-back turned back into a draft."""
import os
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import config  # noqa: E402
import houses  # noqa: E402
import questions  # noqa: E402
import steps  # noqa: E402
from folder import Folder  # noqa: E402
from jobs import Jobs  # noqa: E402

HOUSE = "77-mockup-drive"
LEAVE_OUT = shutil.ignore_patterns(".git", ".venv", "tests", "docs", "_for-testers", "__pycache__", "real-*", "app")
STANDIN = [sys.executable, str(ROOT / "tests" / "app_standin_agent.py")]
DAY = date(2026, 11, 14)
WARNING = ("\n## WARNING: not on the price list (1 items)\n\n| PO number | Description as printed | Qty and unit | "
           "Closest items | Sam's answer (add row / names item / leave unpriced) |\n|---|---|---|---|---|\n"
           "| none | \"Extra stair 1\" | count 1 | Stairwell | |\n")
PICK = ("\n## Pick one\n\n| Row | Item A | Item B | Sam's pick |\n|---|---|---|---|\n"
        "| 2 | Flat ceiling over 10' | Walls over 9' | |\n")


class Check(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT, self.tmp / "f", ignore=LEAVE_OUT)
        self.folder = Folder(self.tmp / "f")
        for stage in ("03 compare", "04 review", "05 request"):
            shutil.rmtree(self.folder.stage(stage, HOUSE))
        self.where = self.folder.stage("02 read", HOUSE)
        self.read_back = self.where / "read-back-1.md"
        seal = self.folder.script("02 read", "seal")
        text = seal.STATUS.sub("status: draft", seal.unsealed(self.read_back.read_text(encoding="utf-8")), count=1)
        for field in ("Answer", "Name", "Date"):
            text = re.sub(rf"^-\s*{field}:.*$", f"- {field}:", text, count=1, flags=re.M)
        self.read_back.write_text(text, encoding="utf-8")
        self.ledger = self.where / "seals.md"
        self.ledger_text = self.ledger.read_text(encoding="utf-8")
        self.ledger.write_text(re.sub(r"^\|\s*read-back-1\.md.*\n", "", self.ledger_text, flags=re.M), encoding="utf-8")
        patcher = mock.patch.object(config, "AGENT_COMMAND", STANDIN)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def plant(self, extra):
        text = self.read_back.read_text(encoding="utf-8")
        self.read_back.write_text(text.replace("## The house", extra.strip() + "\n\n## The house", 1), encoding="utf-8")

    def ask_cell(self, row="3", rule="measured", why="the 13 could be a 18"):
        grid = self.where / "grid-1.md"
        lines = grid.read_text(encoding="utf-8").splitlines()
        header = next(l for l in lines if l.startswith("| # |"))
        col = [c.strip() for c in header.strip().strip("|").split("|")].index(rule)
        for i, line in enumerate(lines):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and cells[0] == row and len(cells) > col:
                cells[col] = f"ask Sam: {why}"
                lines[i] = "| " + " | ".join(cells) + " |"
                break
        grid.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_clean_draft_has_no_cards_and_is_ready(self):
        screen = steps.check_screen(self.folder, HOUSE)
        self.assertEqual((screen["cards"], screen["ready"]), ([], True))

    def test_each_kind_of_question_is_a_card(self):
        self.plant(WARNING + PICK)
        self.ask_cell()
        kinds = sorted(c["kind"] for c in steps.check_screen(self.folder, HOUSE)["cards"])
        self.assertEqual(kinds, ["number", "pick", "warning"])

    def test_question_written_outside_a_table_is_a_card(self):
        self.plant("- Same POs in another house folder: ask Sam: is this the same house dropped in again?")
        found = questions.cards(self.folder, HOUSE)
        self.assertEqual([(c["kind"], c["title"]) for c in found], [("other", "Same POs in another house folder")])
        line = questions.answer_lines(found, {found[0]["id"]: {"words": "No, a different house"}})[0]
        self.assertIn('Sam: "No, a different house"', line)
        self.assertFalse(steps.check_screen(self.folder, HOUSE)["ready"])

    def test_answered_warning_is_no_card(self):
        self.plant(WARNING.replace("| Stairwell | |", "| Stairwell | leave unpriced: Sam |"))
        self.assertEqual(questions.cards(self.folder, HOUSE), [])

    def test_yes_is_written_and_sealed(self):
        steps.read_back_yes(self.folder, Jobs(self.folder), HOUSE, today=DAY)
        text = self.read_back.read_text(encoding="utf-8")
        self.assertIn("status: approved", text)
        self.assertIn("- Answer: yes\n- Name: Sam\n- Date: 2026-11-14", text)
        self.assertEqual(houses.stand(self.folder, HOUSE)["screen"], houses.COMPARE)

    def test_no_yes_while_a_card_is_open(self):
        self.plant(WARNING)
        with self.assertRaises(steps.Stopped):
            steps.read_back_yes(self.folder, Jobs(self.folder), HOUSE, today=DAY)
        self.assertIn("status: draft", self.read_back.read_text(encoding="utf-8"))

    def test_seal_refusal_shows_the_folders_reason_and_leaves_the_draft(self):
        self.ledger.write_text(self.ledger_text, encoding="utf-8")
        before = self.read_back.read_text(encoding="utf-8")
        with self.assertRaises(steps.Stopped) as caught:
            steps.read_back_yes(self.folder, Jobs(self.folder), HOUSE, today=DAY)
        self.assertIn("Stopped before the money", str(caught.exception))
        self.assertEqual(self.read_back.read_text(encoding="utf-8"), before)

    def test_answers_go_to_the_agent_and_make_the_next_read_back(self):
        self.plant(WARNING + PICK)
        self.ask_cell()
        ids = {c["kind"]: c["id"] for c in questions.cards(self.folder, HOUSE)}
        answers = {ids["warning"]: {"choice": "leave"}, ids["pick"]: {"choice": "0"},
                   ids["number"]: {"choice": "fix", "words": "It is 18"}}
        out = self.tmp / "prompt.txt"
        with mock.patch.dict(os.environ, {"STANDIN_PROMPT_OUT": str(out)}):
            jobs = Jobs(self.folder)
            self.assertTrue(steps.send_answers(self.folder, jobs, HOUSE, answers, today=DAY))
            self.assertTrue(jobs.wait(HOUSE))
        text = out.read_text(encoding="utf-8")
        for said in ('Sam: "leave unpriced"', 'Sam picked "Flat ceiling over 10\'"', 'Sam: "It is 18"',
                     "`02 read/77-mockup-drive/read-back-2.md`"):
            self.assertIn(said, text)
        self.assertTrue((self.where / "read-back-2.md").is_file())

    def test_missing_or_stale_answers_are_refused(self):
        self.plant(WARNING)
        card = questions.cards(self.folder, HOUSE)[0]["id"]
        for answers in ({}, {"warning:old": {"choice": "leave"}}, {card: {"choice": "names"}},
                        {card: {"choice": "add"}}):
            with self.subTest(answers=answers), self.assertRaises(steps.Stopped):
                steps.send_answers(self.folder, Jobs(self.folder), HOUSE, answers, today=DAY)

    def test_after_three_rounds_the_screen_stops_with_call_for_help(self):
        self.plant(WARNING)
        for n in (2, 3):
            shutil.copy(self.read_back, self.where / f"read-back-{n}.md")
        screen = steps.check_screen(self.folder, HOUSE)
        self.assertEqual((screen["cards"], screen["ready"]), ([], False))
        self.assertIn("Call for help", screen["blocked"])

    def test_fourth_round_calls_for_help(self):
        self.plant(WARNING)
        for n in (2, 3):
            shutil.copy(self.read_back, self.where / f"read-back-{n}.md")
        card = questions.cards(self.folder, HOUSE)[0]["id"]
        with self.assertRaises(steps.Stopped) as caught:
            steps.send_answers(self.folder, Jobs(self.folder), HOUSE, {card: {"choice": "leave"}}, today=DAY)
        self.assertIn("Call for help", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
