"""Check 6's header reading: the job line, each PO's job name, the date measured and the document
number, against what build_request.header_spec() reads from intake and the next request number."""
import re
from datetime import date, datetime

from request_text import normalise

JOB_LINE = re.compile(r"\bjob (?!name)(.*?) builder\b")
DOCUMENT = re.compile(r"\bvr-(\d+)\b")


MEASURED = re.compile(r"measured on site ([a-z]+ \d{1,2}, \d{4})")


def measured_problems(head, measured):
    """The date measured, printed as 'October 2, 2026', is house-info's date (2026-10-02)."""
    if not measured:
        return []
    m = MEASURED.search(head)
    try:
        printed = datetime.strptime(m.group(1), "%B %d, %Y").date() if m else None
    except ValueError:
        printed = None
    if printed != date.fromisoformat(measured):
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
            problems.append(f"the PO's job name {name} is not in the header")
    problems += measured_problems(head, header.get("measured"))
    want = int(header["document"].split("-")[1])
    found = sorted({int(n) for n in DOCUMENT.findall(text)})
    if found != [want]:
        problems.append(f"the document number must be {header['document']} (the number this commit gives); "
                        f"the request prints {', '.join(f'VR-{n:04d}' for n in found) or 'none'}")
    return problems
