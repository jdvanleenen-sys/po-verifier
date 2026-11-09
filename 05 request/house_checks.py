"""What build and commit check about the house beyond the money: the contractor, the intake files,
the draft PDF they checked, and that one review makes one request."""
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02 read"))
import contractor  # noqa: E402
import intake_read  # noqa: E402

PDF_LINE = re.compile(r"^pdf sha256:\s*([0-9a-f]{64})\s*$", re.M)
FROM_REVIEW = re.compile(r"^from review:\s*(\S.*?)\s*$", re.M)


def gate_problems(root, house, texts):
    """The POs are this folder's contractor's, and intake is as the grid read it."""
    return (contractor.vendor_problems(texts["read-back"])
            + intake_read.problems(Path(root) / "01 intake" / house, texts.get("grid"), house))


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
        m = FROM_REVIEW.search(check.read_text(encoding="utf-8-sig"))
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
