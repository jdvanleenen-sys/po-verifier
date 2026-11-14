"""Where each house stands, worked out from the folder's own files every time it is asked. Nothing
is held only in memory, so a dropped Wi-Fi link or a restarted laptop picks up at the last finished
step. A record that says approved but fails its seal stops the house: the runner never trusts it."""
from folder import highest

NEW, READING, CHECK, COMPARE, DIFFERENCE, PDF, DONE, NO_REQUEST, STOPPED = (
    "new", "reading", "check", "compare", "difference", "pdf", "done", "no-request", "stopped")


def sealed(folder, path):
    """True if the record is approved and its seal and ledger hold; a reason string if it says
    approved but they do not; False if it is still a draft."""
    seal = folder.script("02 read", "seal")
    text = seal.read_record(path)
    if not seal.is_approved(text):
        return False
    problems = seal.file_approval_problems(path, text)
    return "; ".join(problems) if problems else True


def _after_read(folder, house):
    variance = highest(folder.stage("03 compare", house), "variance")
    if variance is None:
        return COMPARE, None
    review = highest(folder.stage("04 review", house), "review")
    review_state = sealed(folder, review) if review else False
    if isinstance(review_state, str):
        return STOPPED, review_state
    if not review_state:
        return DIFFERENCE, None
    if "nothing to ask for" in review.read_text(encoding="utf-8").lower():
        return NO_REQUEST, None
    if highest(folder.stage("05 request", house), "vpo-request", ".pdf"):
        return DONE, None
    return PDF, None


def stand(folder, house, running=False):
    """{"house", "screen", "reason", "busy"} for one house. running: a job for this house is under
    way, so the screen shows it waiting; the files still say which screen it is on."""
    if not folder.stage("01 intake", house).is_dir():
        return {"house": house, "screen": NEW, "reason": None, "busy": False}
    screen, reason = READING, None
    read_back = highest(folder.stage("02 read", house), "read-back")
    if read_back is not None:
        state = sealed(folder, read_back)
        if isinstance(state, str):
            screen, reason = STOPPED, state
        elif not state:
            screen = CHECK
        else:
            screen, reason = _after_read(folder, house)
    return {"house": house, "screen": screen, "reason": reason, "busy": bool(running)}


def all_houses(folder, running=()):
    return [stand(folder, h, h in running) for h in folder.houses()]
