"""Each step of one house, in order. Every step checks the files first, so a repeated tap or a
restart never does a step twice. Steps 3 to 6 are added as they are built."""
import json
from datetime import date

import agent
import config
import difference
import houses
import questions
import request_pdf
import sam_yes
from folder import highest

MAX_ROUNDS = 3


class Stopped(Exception):
    """A plain-words reason a step did not run."""


def _before_read(folder, house):
    path = folder.root / config.APP_DIR / house / "before-read.json"
    if not path.is_file():
        raise Stopped(f"{house} was not locked by the app, so its answers before the read are missing.")
    return json.loads(path.read_text(encoding="utf-8"))


def read_answers(before):
    """Sam's answers before the read, as lines for the read prompt."""
    measured = before["measured"]
    lines = [f"- Date measured: not recorded (Sam, {before['locked']})." if measured == "not recorded"
             else f"- Date measured: {measured} (Sam)."]
    for answer in before["answers"].values():
        lines.append(f"- {answer['ask']} Sam: \"Yes, these are the POs for {before['address']}.\" ({answer['date']})")
    return "\n".join(lines)


def start_read(folder, jobs, house):
    """Start the read for a locked house. Refused unless the house is on the Reading screen with no
    read-back yet; True if started, False if a read is already running."""
    state = houses.stand(folder, house, house in jobs.running())
    if state["screen"] != houses.READING:
        raise Stopped(f"{house} is past the read.")
    if state["busy"]:
        return False
    text = agent.prompt("read", house=house, answers=read_answers(_before_read(folder, house)))
    return jobs.start(house, "read", text)


def _draft(folder, jobs, house):
    """The house's highest read-back, if the house is on the Check screen and not busy."""
    state = houses.stand(folder, house, house in jobs.running())
    if state["screen"] != houses.CHECK:
        raise Stopped(f"{house} is not waiting on a check.")
    if state["busy"]:
        raise Stopped("The reader is still working on this house.")
    return highest(folder.stage("02 read", house), "read-back")


def check_screen(folder, house):
    """{"cards", "ready", "blocked"}: ready when no card is open and grid.py check --final passes;
    blocked holds the folder's reason when no card is open but the check still refuses."""
    open_cards = questions.cards(folder, house)
    if open_cards:
        return {"cards": open_cards, "ready": False, "blocked": None}
    passed, output = sam_yes.script(folder, "02 read/grid.py", "check", house, "--final")
    return {"cards": [], "ready": passed, "blocked": None if passed else output}


def send_answers(folder, jobs, house, answers, today=None):
    """Start the agent on the next read-back with Sam's card answers. Refused after MAX_ROUNDS."""
    read_back = _draft(folder, jobs, house)
    attempt = int(read_back.stem.rsplit("-", 1)[1])
    if attempt >= MAX_ROUNDS:
        raise Stopped("Three rounds of questions and still not settled. Call for help.")
    try:
        lines = questions.answer_lines(questions.cards(folder, house), answers)
    except ValueError as err:
        raise Stopped(str(err))
    text = agent.prompt("answers", house=house, read_back=read_back.name,
                        next_read_back=f"read-back-{attempt + 1}.md", next_read_back_stem=f"read-back-{attempt + 1}",
                        today=(today or date.today()).isoformat(), answers="\n".join(lines))
    return jobs.start(house, "answers", text)


def read_back_yes(folder, jobs, house, today=None):
    """Sam tapped That's all right: write his yes on the highest read-back and seal it."""
    read_back = _draft(folder, jobs, house)
    screen = check_screen(folder, house)
    if not screen["ready"]:
        raise Stopped(screen["blocked"] or "Answer every card first.")
    try:
        sam_yes.seal(folder, read_back, sam_yes.painter_name(folder), (today or date.today()).isoformat())
    except sam_yes.Refused as err:
        raise Stopped(f"Stopped before the money: {err}")


def run_compare(folder, house):
    """compare.py, by code, once the read-back is sealed. No AI."""
    if houses.stand(folder, house)["screen"] != houses.COMPARE:
        raise Stopped(f"{house} is not waiting on the compare.")
    passed, output = sam_yes.script(folder, "03 compare/compare.py", house)
    if not passed:
        raise Stopped(f"Stopped before the money: {output}")
    return output


def review_yes(folder, house, picks, today=None, none_reason=""):
    """Sam tapped Build the PDF: write his picks into review-N.md and seal it with his yes. A review
    the folder refuses is taken back out, so the next try uses the same number."""
    if houses.stand(folder, house)["screen"] != houses.DIFFERENCE:
        raise Stopped(f"{house} is not on the Difference screen.")
    try:
        text = difference.review_text(folder, house, picks, none_reason)
    except ValueError as err:
        raise Stopped(str(err))
    attempt = text.split("attempt: ", 1)[1].split("\n", 1)[0]
    path = folder.stage("04 review", house) / f"review-{attempt}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    try:
        sam_yes.seal(folder, path, sam_yes.painter_name(folder), (today or date.today()).isoformat())
    except sam_yes.Refused as err:
        path.unlink()
        raise Stopped(f"Stopped before the money: {err}")


def start_request(folder, jobs, house):
    """After the review is sealed: the agent fills the request layout and builds the draft with
    Sam's notes answer. Code checks the result; the agent never numbers it."""
    state = houses.stand(folder, house, house in jobs.running())
    if state["screen"] != houses.PDF:
        raise Stopped(f"{house} is not ready for its request.")
    if state["busy"]:
        return False
    notes = request_pdf.notes_answer(folder, house)
    if notes is None:
        raise Stopped("Say whether your site notes go with the request first.")
    today = date.today().strftime("%B %d, %Y").replace(" 0", " ")
    return jobs.start(house, "request", agent.prompt("request", house=house, notes=notes, today=today))


def approve(folder, jobs, house, today=None):
    """Sam tapped Approve: the folder's commit numbers the draft only if its six checks pass again,
    then his yes to send is written. A second tap finds the house done and gives the same number."""
    state = houses.stand(folder, house, house in jobs.running())
    if state["screen"] == houses.DONE:
        return request_pdf.numbered(folder, house).name
    if state["screen"] != houses.PDF or state["busy"]:
        raise Stopped(f"{house} has no request ready to approve.")
    if not request_pdf.draft(folder, house)["passed"]:
        raise Stopped("Stopped before the money: the request's six checks have not all passed.")
    passed, output = sam_yes.script(folder, "05 request/build_request.py", "commit", house)
    if not passed:
        raise Stopped(f"Stopped before the money: {output}")
    pdf = request_pdf.numbered(folder, house)
    check = pdf.with_name(pdf.name.replace("vpo-request-", "request-check-").replace(".pdf", ".md"))
    request_pdf.write_send_yes(check, sam_yes.painter_name(folder), (today or date.today()).isoformat())
    return pdf.name
