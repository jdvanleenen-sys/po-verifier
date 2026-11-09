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
