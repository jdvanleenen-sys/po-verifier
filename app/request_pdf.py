"""The Your PDF screen: Sam's notes answer, the draft request and its six checks as the script wrote
them, and Approve, which runs the folder's commit and writes his yes to send. The app never sends."""
import json
import re

import config
from folder import highest

NOTES = ("yes", "no", "yes-other-house")
NUMBERED = re.compile(r"vpo-request-(\d+)\.pdf")
PASS = re.compile(r":\s*pass:", re.I)
CHECK = re.compile(r"^\s*-?\s*([1-6])[a-z]?\.\s")


def _record(folder, house):
    return folder.root / config.APP_DIR / house / "request.json"


def save_notes(folder, house, notes):
    """Sam's answer to "attach your site notes?", kept for the build. A notes page that covers other
    houses takes only yes-other-house (his yes in those words) or no."""
    if notes not in NOTES:
        raise ValueError("Say whether your site notes go with the request.")
    shared = "covers two houses" in (folder.stage("01 intake", house) / "house-info.md").read_text(encoding="utf-8")
    if shared and notes == "yes":
        raise ValueError("Your notes page shows other houses too. Say yes to sending it with those houses on it, or no.")
    if not shared and notes == "yes-other-house":
        notes = "yes"
    path = _record(folder, house)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"notes": notes}), encoding="utf-8", newline="\n")
    return notes


def notes_answer(folder, house):
    path = _record(folder, house)
    return json.loads(path.read_text(encoding="utf-8"))["notes"] if path.is_file() else None


def shared_notes(folder, house):
    info = folder.stage("01 intake", house) / "house-info.md"
    return info.is_file() and "covers two houses" in info.read_text(encoding="utf-8")


def draft(folder, house):
    """{"pdf", "checks", "passed"}: the draft PDF path (or None), the six check lines, and whether
    all six read pass. Read from the script's own script-checks.md, never from the agent's word."""
    where = folder.stage("05 request", "drafts") / house
    pdf, checks = where / "vpo-request.pdf", where / "script-checks.md"
    review = highest(folder.stage("04 review", house), "review")
    stale = review is not None and checks.is_file() and checks.stat().st_mtime < review.stat().st_mtime
    if not pdf.is_file() or not checks.is_file() or stale:
        # A draft built before the current review is from an earlier attempt: never shown or approved.
        return {"pdf": None, "checks": [], "passed": False}
    lines = [l.strip().lstrip("- ") for l in checks.read_text(encoding="utf-8").splitlines() if CHECK.match(l)]
    numbers = {CHECK.match(l).group(1) for l in checks.read_text(encoding="utf-8").splitlines() if CHECK.match(l)}
    # Every line must say pass. A "cannot check" or any other word stops before Approve.
    passed = numbers == set("123456") and all(PASS.search(l) for l in lines)
    return {"pdf": pdf, "checks": lines, "passed": passed}


def numbered(folder, house):
    """The highest numbered request PDF for the house, or None."""
    return highest(folder.stage("05 request", house), "vpo-request", ".pdf")


def write_send_yes(path, name, day):
    """Sam's yes to send in a numbered request check. sent: stays blank until he says he sent it."""
    text = path.read_text(encoding="utf-8")
    pdf = path.name.replace("request-check-", "vpo-request-").replace(".md", ".pdf")
    for field, value in (("Answer", f"yes, to {pdf} as shown"), ("Name", name), ("Date", day)):
        text, n = re.subn(rf"^-\s*{field}:.*$", f"- {field}: {value}", text, count=1, flags=re.M)
        if not n:
            raise ValueError(f"{path.name} has no {field} line under Sam's yes to send.")
    path.write_text(text, encoding="utf-8", newline="\n")


def yes_missing(path):
    """True when a numbered request check has no answer under Sam's yes to send."""
    return path.is_file() and re.search(r"^-\s*Answer:[ \t]*$", path.read_text(encoding="utf-8"), re.M) is not None


def mark_sent(path):
    text = path.read_text(encoding="utf-8")
    text, n = re.subn(r"^-\s*sent:.*$", "- sent: yes", text, count=1, flags=re.M)
    if not n:
        raise ValueError(f"{path.name} has no sent line.")
    path.write_text(text, encoding="utf-8", newline="\n")
