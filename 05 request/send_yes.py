"""Check Sam's yes to send in a numbered request check, after it is written.

  python "05 request/send_yes.py" <house> [N]

Reads 05 request/<house>/request-check-N.md (the highest N if none is given) and refuses its
"Sam's yes to send" block unless it holds a plain yes ("yes", or "yes, to vpo-request-N.pdf as
shown" naming this check's own request; "Yes, but..." or "Yes?" is not a yes), his name, a date
written as YYYY-MM-DD and not after today, and a sent line that is blank (not sent yet), "yes"
alone, or "no" (a note may follow a no). Exit 0 and one line when it passes; exit 1 and every problem when it does not.

Why: an outside tester (2026-11-19) wrote "Yes, but this is practice..." in the block and nothing
refused it, though the folder's rules say a yes with a condition is not a yes.
"""
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import seal  # noqa: E402

HEADING = re.compile(r"^##\s*Sam's yes to send\s*$", re.M | re.I)
SENT_LINE = re.compile(r"^-\s*sent:[ \t]*(.*?)\s*$", re.M | re.I)


SENT_OK = re.compile(r"(yes\.?|no\b.*|)", re.I | re.S)


def latest(house_dir):
    found = [(int(m.group(1)), p) for p in Path(house_dir).glob("request-check-*.md")
             if (m := re.match(r"request-check-(\d+)\.md$", p.name))]
    return max(found)[1] if found else None


def problems(text, today=None, pdf="vpo-request-N.pdf"):
    """Every problem with the send block of a request check's text; [] when it passes."""
    head = HEADING.search(text)
    if not head:
        return ["has no \"Sam's yes to send\" block. It is written by build_request.py commit; never remove it"]
    block = text[head.end():]
    as_shown = re.compile(rf"yes,?\s+to\s+{re.escape(pdf)}\s+as shown\.?", re.I)
    said = seal.ANSWER.search(block)
    if said and as_shown.fullmatch(said.group(1).strip()):  # the send form of a plain yes
        block = seal.ANSWER.sub("- Answer: yes", block, count=1)
    found = seal.yes_problems(block)
    day = seal.DATE.search(block)
    when = day.group(1).strip() if day else ""
    if seal.ISO_DAY.fullmatch(when) and when > (today or datetime.date.today().isoformat()):
        found.append(f"has a Date under Sam's yes that is after today: {when}")
    sent = SENT_LINE.search(block)
    if not sent:
        found.append("has no sent line under Sam's yes. It is written by build_request.py commit; never remove it")
    elif not SENT_OK.fullmatch(sent.group(1).strip()):
        found.append(f"has a sent line that is not yes, no or blank: '{sent.group(1).strip()}'. "
                     "Write yes alone, and only once Sam has sent it")
    return found


def main(argv):
    if len(argv) < 2:
        sys.exit('Use: python "05 request/send_yes.py" <house> [N]')
    house_dir = ROOT / "05 request" / argv[1]
    path = house_dir / f"request-check-{argv[2]}.md" if len(argv) > 2 else latest(house_dir)
    if path is None or not path.is_file():
        sys.exit(f"No request check for {argv[1]} in 05 request/.")
    pdf = path.name.replace("request-check-", "vpo-request-").replace(".md", ".pdf")
    found = problems(seal.read_record(path), pdf=pdf)
    if found:
        sys.exit(f"{path.name}: Sam's yes to send is refused:\n- " + "\n- ".join(found))
    print(f"{path.name}: Sam's yes to send is a plain yes, with his name and the date.")


if __name__ == "__main__":
    main(sys.argv)
