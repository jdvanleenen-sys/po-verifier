"""What build and commit check about the house beyond the money: the contractor, the intake files,
the draft PDF they checked, and that one review makes one request."""
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02 read"))
import contractor  # noqa: E402
import intake_read  # noqa: E402
import seal  # noqa: E402

import records  # noqa: E402  (05 request, beside this file)

PDF_LINE = re.compile(r"^pdf sha256:\s*([0-9a-f]{64})\s*$", re.M)
FROM_REVIEW = re.compile(r"^from review:\s*(\S.*?)\s*$", re.M)


def gate_problems(root, house, texts):
    """The POs are this folder's contractor's, intake is as the grid read it, no row is asked for
    twice, and work on no PO follows the standing answer."""
    root = Path(root)
    setup = root / "reference" / "contractor.md"
    return (contractor.vendor_problems(texts["read-back"])
            + intake_read.problems(root / "01 intake" / house, texts.get("grid"), house)
            + intake_read.since_first_problems(root / "01 intake" / house, root / "02 read" / house, house,
                                               below=intake_read.latest_number(root / "02 read" / house))
            + sent_problems(root, root / "05 request" / house, texts["review"])
            + standing_epo_problems(texts["review"], setup.read_text(encoding="utf-8-sig") if setup.is_file() else ""))


SENT = re.compile(r"^-?\s*sent:\s*yes\b", re.I | re.M)


def on_rows(review_text):
    """{(PO number, item): row number} for every row Sam put on, read the way money.decisions reads it."""
    rows = records.section(records.tables(review_text), "")
    return {(records.column(r, "po number").strip().lower(), records.column(r, "item").strip().lower()):
            records.column(r, "row").strip() for r in rows
            if records.decision_word(records.column(r, "sam's decision")) == "on"}


def sent_problems(root, house_dir, review_text):
    """Every row of this review that is already on a request marked sent: yes. A sent row is chased
    again through 06 outcome, never by a second request."""
    problems, now = [], on_rows(review_text)
    for check in sorted(Path(house_dir).glob("request-check-*.md")):
        text = seal.read_record(check)
        m = FROM_REVIEW.search(text)
        if not SENT.search(text) or not m or not (Path(root) / m.group(1)).is_file():
            continue
        before = on_rows(seal.read_record(Path(root) / m.group(1)))
        pdf = check.name.replace("request-check-", "vpo-request-").replace(".md", ".pdf")
        for (po, item), num in now.items():
            if (po, item) in before:
                problems.append(f"row {num} ({item}) was already asked for on {pdf}, sent. Ask Sam: a re-ask "
                                "goes through 06 outcome, not a second request")
    return problems


ASK_EACH_TIME = ("ask each time", "not asked", "none", "not decided")


def standing_epo_problems(review_text, setup_text):
    """With a standing answer for work on no PO, a chosen row on no PO names its PO in 'EPO goes on',
    unless the reason gives Sam's own different answer ("Sam: ...")."""
    rule = contractor.answer(setup_text, "Work on no PO goes on").strip()
    if not rule or rule.lower().startswith(ASK_EACH_TIME):
        return []
    problems = []
    for r in records.section(records.tables(review_text), ""):
        if (records.column(r, "po number").strip().lower() == "none"
                and records.decision_word(records.column(r, "sam's decision")) == "on"
                and not records.column(r, "epo goes on").strip()
                and "sam:" not in records.column(r, "reason").lower()):
            problems.append(f"review row {records.column(r, 'row').strip()} ({records.column(r, 'item').strip()}) is on "
                            "no PO and 'EPO goes on' is blank, but the standing answer in contractor.md says: "
                            f"{rule}. Fill EPO goes on, or write Sam's different answer in the reason as 'Sam: ...'")
    return problems


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pdf_problem(pdf, checks_text):
    """The draft PDF is the one build checked: its sha256 is the one build wrote."""
    m = PDF_LINE.search(checks_text)
    if not m:
        return "script-checks.md does not record the draft PDF's sha256. Build again."
    if m.group(1) != sha256(pdf):
        return "the draft PDF changed after it was built and checked. Build it again."
    return None


def review_used(house_dir, review_name):
    """The numbered request that already comes from this review file, or None."""
    for check in sorted(Path(house_dir).glob("request-check-*.md")):
        m = FROM_REVIEW.search(seal.read_record(check))
        if m and m.group(1) == review_name:
            return check.name.replace("request-check-", "vpo-request-").replace(".md", ".pdf")
    return None


LOT = re.compile(r"LOT/BLOCK(?:/UNIT)?:?\s*([\d/]+)")


def lot_from_pos(texts):
    """The lot and block numbers when every PO and EPO that prints one prints the same; else None."""
    found = {tuple(re.findall(r"\d+", m.group(1))) for t in texts if (m := LOT.search(t))}
    return list(found.pop()) if len(found) == 1 else None


def next_free(folder, stem):
    """The next free file name for a numbered record, such as read-back-3.md."""
    taken = [int(m.group(1)) for p in Path(folder).glob(f"{stem}-*.md")
             if (m := re.match(rf"{re.escape(stem)}-(\d+)\.md$", p.name))]
    return f"{stem}-{max(taken, default=0) + 1}.md"


def fix_advice(root, house):
    """How to correct records that do not agree, with the real next numbers and no circle."""
    root = Path(root)
    read_back = next_free(root / "02 read" / house, "read-back")
    review = next_free(root / "04 review" / house, "review")
    return ("To fix: never edit a file Sam approved. If the read-back is wrong, write " + read_back +
            " with the correction, show it to Sam and seal his yes; compare.py then writes a new variance "
            "from it. A variance is never written or corrected by hand. If only the review is wrong, write "
            + review + " from the variance, show it to Sam and seal his yes. Then build again.")


SNAPSHOT = ("snapshot price-list", "has changed since the read-back was made")
VARIANCE_EDIT = ("says po amount", "measured qty", "agreed rate", "po qty or rate differs")


def stop_message(root, house, problems):
    """The problems to print, each once, and the one fix that fits them. A missing or changed
    snapshot makes every row fail its price, so only the snapshot lines are shown then."""
    shown = list(dict.fromkeys(problems))
    snapshot = [p for p in shown if any(s in p for s in SNAPSHOT)]
    if snapshot:
        return snapshot, ("To fix: put the original price list snapshot back. A snapshot is never edited or "
                          "deleted. If it is lost, take a new snapshot, write "
                          + next_free(Path(root) / "02 read" / house, "read-back")
                          + " from it, show it to Sam and seal his yes.")
    if any(p.startswith("variance row") and any(v in p.lower() for v in VARIANCE_EDIT) for p in shown):
        return shown, ("To fix: never edit a variance. Delete the variance file that was changed and run "
                       "compare.py again from the approved read-back.")
    return shown, fix_advice(root, house)


HTML_LINE = re.compile(r"^html sha256:\s*([0-9a-f]{64})\s*$", re.M)


def html_problem(html, checks_text):
    """request.html is the one build printed: its sha256, not its file time (a copy or a sync moves
    file times without changing a byte)."""
    m = HTML_LINE.search(checks_text)
    if not m:
        return "script-checks.md does not record request.html's sha256. Build again."
    if not Path(html).is_file() or m.group(1) != sha256(html):
        return "request.html changed after the last build. Build again."
    return None


FROM_LINE = re.compile(r"FROM:\s*(.*?)\s+-\s+(.*?)\s+ADDRESS:")
YES_DATE = re.compile(r"^-\s*Date:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)


def header_extras(texts, review_text):
    """What else the header must agree with: the builder and community every PO prints on its FROM
    line (None when the POs print none or disagree), and the date of Sam's yes on the review."""
    found = {(m.group(1).strip(), m.group(2).strip()) for t in texts if (m := FROM_LINE.search(t))}
    builder, community = found.pop() if len(found) == 1 else (None, None)
    yes = YES_DATE.search(review_text or "")
    return {"po_builder": builder, "community": community, "review_date": yes.group(1) if yes else None}
