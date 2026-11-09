"""Check 6's header reading: the job line, each PO's job name, the date measured, the trade
contractor, the builder and the document number, against what build_request.header_spec() reads
from intake, reference/contractor.md and the next request number."""
import re
from datetime import date, datetime

from request_text import normalise

JOB_LINE = re.compile(r"\bjob (?!name)(.*?) builder\b")
DOCUMENT = re.compile(r"\bvr-(\d+)\b")


MEASURED = re.compile(r"measured on site ([a-z]+ \d{1,2}, \d{4})")
TRADE = re.compile(r"\btrade contractor (.*?) prepared\b")
BUILDER = re.compile(r"\bbuilder (.*?) trade contractor\b")


def who_problems(head, header):
    """The trade contractor is reference/contractor.md's, as set up; the builder is one he named."""
    problems = []
    if "contractor" in header:
        m = TRADE.search(head)
        printed = m.group(1).strip() if m else ""
        if printed != normalise(header["contractor"]):
            problems.append(f"the trade contractor reads '{printed}'; reference/contractor.md gives "
                            f"'{header['contractor']}'. The request goes out under this folder's contractor only")
    if "builders" in header:
        m = BUILDER.search(head)
        printed = m.group(1).strip() if m else ""
        if not printed or printed not in normalise(header["builders"]):
            problems.append(f"the builder reads '{printed}'; reference/contractor.md names the builders as "
                            f"'{header['builders']}'")
    return problems


def measured_problems(head, measured):
    """The date measured, printed as 'October 2, 2026', is house-info's date (2026-10-02)."""
    if not measured:
        return []
    try:
        wanted = date.fromisoformat(measured)
    except ValueError:
        return [f"house-info gives the date measured as {measured}, which is not a real date. Ask Sam for the date"]
    m = MEASURED.search(head)
    try:
        printed = datetime.strptime(m.group(1), "%B %d, %Y").date() if m else None
    except ValueError:
        printed = None
    if printed != wanted:
        return [f"the date measured reads '{m.group(1) if m else ''}'; house-info gives {measured}"]
    return []


def header_problems(request_pages, header):
    """The job line carries exactly the house's address and lot numbers, every PO's job name is in
    the header, and the only document number printed is the one the commit will give."""
    text = normalise(" ".join(request_pages))
    head = text[:text.find("before tax")] if "before tax" in text else text
    problems, job = [], JOB_LINE.search(head)
    if header["job_numbers"] is not None:
        printed = sorted(re.findall(r"\d+", job.group(1))) if job else None
        if printed != sorted(header["job_numbers"]):
            problems.append(f"the job line reads '{job.group(1) if job else ''}'; house-info gives the numbers "
                            + ", ".join(header["job_numbers"]))
    if not header["job_names"] and header["job_numbers"] is None:
        problems.append("nothing to check the job line against: the POs give no job name and house-info "
                        "gives no address or lot. Fill in house-info.md in 01 intake")
    for name in header["job_names"]:
        if normalise(name) not in head:
            problems.append(f"the PO's job name {name} is not in the header. Check that PO is for this "
                            "house: a PO for another house comes out of intake (ask Sam), it never goes in the header")
    problems += measured_problems(head, header.get("measured"))
    problems += who_problems(head, header)
    want = int(header["document"].split("-")[1])
    found = sorted({int(n) for n in DOCUMENT.findall(text)})
    if found != [want]:
        problems.append(f"the request prints {', '.join(f'VR-{n:04d}' for n in found) or 'no document number'}; "
                        f"this commit would number it {header['document']}. The number comes from the commit, "
                        "never typed by hand; if a request from this review is already numbered, a new one "
                        "needs a new review with Sam's yes")
    return problems
