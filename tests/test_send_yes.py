"""Sam's yes to send is checked like every other yes. Run from the repo root:

    python -m unittest discover -s tests -v

An outside tester (2026-11-19) wrote "Yes, but this is practice, so it is not being sent" in a
request check's send block and nothing refused it. send_yes.py now does.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "05 request"))
import send_yes  # noqa: E402

HEAD = "# house, request check 1\n\n- 1. ...: pass: ok\n\nSite notes attached as proof: yes\n\n## Sam's yes to send\n"


def check(answer="yes", name="Sam", date="2026-11-19", sent="no"):
    return HEAD + f"- Answer: {answer}\n- Name: {name}\n- Date: {date}\n- sent: {sent}\n"


class SendYes(unittest.TestCase):
    def found(self, text):
        return send_yes.problems(text, today="2026-11-19", pdf="vpo-request-1.pdf")

    def test_a_plain_yes_passes_sent_or_not(self):
        self.assertEqual(self.found(check()), [])
        self.assertEqual(self.found(check(answer="Yes.", sent="yes")), [])

    def test_the_send_form_and_a_not_yet_sent_line_pass(self):
        self.assertEqual(self.found(check(answer="yes, to vpo-request-1.pdf as shown", sent="")), [])
        self.assertEqual(self.found(check(sent="no (practice run; nothing was sent)")), [])

    def test_the_send_form_naming_another_request_is_refused(self):
        self.assertTrue(self.found(check(answer="yes, to vpo-request-2.pdf as shown")))

    def test_a_sent_line_with_a_condition_is_refused(self):
        found = self.found(check(sent="yes, but only the first page"))
        self.assertTrue(any("not yes, no or blank" in p for p in found), found)

    def test_the_sample_house_passes(self):
        path = ROOT / "05 request" / "77-mockup-drive" / "request-check-1.md"
        self.assertEqual(send_yes.problems(path.read_text(encoding="utf-8"), pdf="vpo-request-1.pdf"), [])

    def test_yes_but_is_refused(self):
        found = self.found(check(answer="Yes, but this is practice, so it is not being sent."))
        self.assertTrue(any("not a plain yes" in p for p in found), found)

    def test_blank_answer_name_and_date_are_refused(self):
        found = self.found(check(answer="", name="", date=""))
        self.assertTrue(any("no Answer" in p for p in found))
        self.assertTrue(any("no Name" in p for p in found))
        self.assertTrue(any("no Date" in p for p in found))

    def test_a_future_date_is_refused(self):
        found = self.found(check(date="2099-01-01"))
        self.assertTrue(any("after today" in p for p in found))

    def test_a_check_with_no_send_block_is_refused(self):
        self.assertTrue(self.found(HEAD.replace("## Sam's yes to send\n", "")))

    def test_the_committed_template_block_is_refused_until_filled(self):
        self.assertTrue(self.found((ROOT / "templates" / "request-check.md").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
