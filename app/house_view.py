"""What each screen shows for a house, and what each tap does, built from the steps. Kept apart from
server.py so the routes stay thin and this can be tested without a web server."""
import re

import difference
import houses
import request_pdf
import steps
from folder import highest

PHOTOS = (".jpg", ".jpeg", ".png")


def _address(folder, house):
    info = folder.stage("01 intake", house) / "house-info.md"
    found = re.search(r"^-\s*Address:[ \t]*(\S.*)$", info.read_text(encoding="utf-8"), re.M) if info.is_file() else None
    return found.group(1).strip() if found else house


def note_photos(folder, house):
    """The house's notes photos in intake, for the zoom on the Check screen."""
    intake = folder.stage("01 intake", house)
    return sorted(p for p in intake.iterdir() if p.is_file() and p.suffix.lower() in PHOTOS)


def summary(folder, jobs):
    running = jobs.running()
    return [{**s, "address": _address(folder, s["house"])} for s in houses.all_houses(folder, running)]


def _rows_read(folder, house):
    read_back = highest(folder.stage("02 read", house), "read-back")
    gr = folder.script("02 read", "grid_read")
    rows = gr.as_dicts(gr.under(read_back.read_text(encoding="utf-8"), "rows"))
    return [{"row": r.get("#", ""), "line": r.get("line as printed", ""), "measured": r.get("sam measured", ""),
             "item": r.get("price list item", "")} for r in rows]


def _screen_data(folder, house, screen):
    if screen == houses.CHECK:
        return {**steps.check_screen(folder, house), "rows": _rows_read(folder, house),
                "photos": len(note_photos(folder, house))}
    if screen == houses.DIFFERENCE:
        return {**difference.screen(folder, house), "shared_notes": request_pdf.shared_notes(folder, house)}
    if screen == houses.PDF:
        shown = request_pdf.draft(folder, house)
        return {"checks": shown["checks"], "passed": shown["passed"], "has_pdf": shown["pdf"] is not None,
                "notes": request_pdf.notes_answer(folder, house)}
    if screen == houses.DONE:
        pdf = request_pdf.numbered(folder, house)
        check = pdf.with_name(pdf.name.replace("vpo-request-", "request-check-").replace(".pdf", ".md"))
        text = check.read_text(encoding="utf-8") if check.is_file() else ""
        day = re.search(r"^-\s*Date:[ \t]*(\S+)", text, re.M)
        return {"pdf": pdf.name, "document": "VR-" + pdf.stem.rsplit("-", 1)[1].zfill(4),
                "approved": day.group(1) if day else None, "sent": "- sent: yes" in text}
    return {}


def detail(folder, jobs, house):
    """Everything the phone needs for this house's current screen. A house waiting on the compare
    runs it here (code only), so the phone never shows a step with nothing to do."""
    state = houses.stand(folder, house, house in jobs.running())
    if state["screen"] == houses.COMPARE and not state["busy"]:
        steps.run_compare(folder, house)
        state = houses.stand(folder, house, False)
    data = {**state, "address": _address(folder, house), "job": jobs.status(house)}
    if not state["busy"]:
        data.update(_screen_data(folder, house, state["screen"]))
    return data


def _review(folder, jobs, house, body):
    picks = {str(k): v for k, v in (body.get("picks") or {}).items()}
    request_pdf.save_notes(folder, house, body.get("notes"))
    steps.review_yes(folder, house, picks)
    if houses.stand(folder, house)["screen"] == houses.PDF:
        steps.start_request(folder, jobs, house)


def _retry(folder, jobs, house):
    screen = houses.stand(folder, house, house in jobs.running())["screen"]
    if screen == houses.READING:
        return steps.start_read(folder, jobs, house)
    if screen == houses.PDF:
        return steps.start_request(folder, jobs, house)
    raise steps.Stopped("Nothing to run again on this screen.")


def act(folder, jobs, house, action, body):
    """One tap. Returns extra fields for the answer, or None."""
    if action == "answers":
        steps.send_answers(folder, jobs, house, body.get("answers") or {})
    elif action == "yes":
        steps.read_back_yes(folder, jobs, house)
        steps.run_compare(folder, house)
    elif action == "review":
        _review(folder, jobs, house, body)
    elif action == "approve":
        return {"pdf": steps.approve(folder, jobs, house)}
    elif action == "sent":
        pdf = request_pdf.numbered(folder, house)
        if pdf is None:
            raise steps.Stopped("There is no request to mark as sent.")
        request_pdf.mark_sent(pdf.with_name(pdf.name.replace("vpo-request-", "request-check-").replace(".pdf", ".md")))
    elif action == "stop":
        jobs.stop(house)
    elif action == "retry":
        _retry(folder, jobs, house)
    else:
        raise steps.Stopped("That is not something this screen can do.")
    return None
