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
COMMUNITY = re.compile(r"\bcommunity (.*?) measured on site\b")
PREPARED = re.compile(r"\bprepared ([a-z]+ \d{1,2}, \d{4})\b")
NOT_RECORDED = re.compile(r"measured on site (?:date )?not (?:recorded|given)\b")
HOW_THEY_ARRIVE = re.compile(r",\s*(?:through|pos?|by)\b.*$", re.I | re.S)


def named_builders(answer):
    """The builders contractor.md names, each whole, without how the POs arrive:
    'A Homes; B Ltd., through SupplyPro' gives ['a homes', 'b ltd.']."""
    names = (normalise(HOW_THEY_ARRIVE.sub("", part)) for part in (answer or "").split(";"))
    return [n for n in names if n]


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
        if not printed or printed not in named_builders(header["builders"]):
            problems.append(f"the builder reads '{printed}'; reference/contractor.md names the builders as "
                            f"'{header['builders']}'")
    return problems


def facts_problems(head, header):
    """The community and builder every PO prints, and a prepared date between Sam's yes on the
    review and today. Each is checked only when the build knows it."""
    problems = []
    for key, pattern, label in (("community", COMMUNITY, "community"), ("po_builder", BUILDER, "builder")):
        if header.get(key):
            m = pattern.search(head)
            printed = m.group(1).strip() if m else ""
            if printed != normalise(header[key]):
                problems.append(f"the {label} reads '{printed}'; every PO prints '{header[key]}'")
    if header.get("review_date"):
        m = PREPARED.search(head)
        try:
            printed = datetime.strptime(m.group(1), "%B %d, %Y").date() if m else None
        except ValueError:
            printed = None
        try:
            start = date.fromisoformat(header["review_date"])
        except ValueError:
            return problems + [f"the review's Date under Sam's yes, {header['review_date']}, is not a real day. "
                               "A review is never edited after the yes: write the next review with the right date"]
        if printed is None or not start <= printed <= date.today():
            problems.append(f"the prepared date reads '{m.group(1) if m else ''}'; it must be between Sam's yes on "
                            f"the review ({start:%B} {start.day}, {start.year}) and today")
    return problems


def measured_problems(head, measured, known=False):
    """The date measured, printed as 'October 2, 2026', is house-info's date (2026-10-02). When the
    build knows house-info gives no date (known), the header must say the date is not recorded."""
    if not measured and known:
        if MEASURED.search(head) or not NOT_RECORDED.search(head):
            return ["house-info gives no date measured, so the header must read 'Measured on site: Date not "
                    "recorded'. Never print a date Sam did not give"]
        return []
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


def job_text_problems(job, header):
    """The job line holds house-info's address word for word, and the lot as 'lot <lot>, block
    <block>' in that order, so swapped or moved digits are refused (the sorted digits can agree)."""
    problems, job = [], normalise(job)
    address = normalise(header.get("address") or "")
    if address and not re.search(rf"(?<![\w-]){re.escape(address)}(?![\w-])", job):
        problems.append(f"the job line reads '{job}', but house-info gives the address '{header['address']}' "
                        "word for word")
    lot = header.get("lot") or []
    if lot:
        want = f"lot {lot[0]}, block {lot[1]}" if len(lot) > 1 else f"lot {lot[0]}"
        if not re.search(rf"(?<!\w){re.escape(want)}(?!\w)", job):
            problems.append(f"the job line reads '{job}'; the lot must read '{want}' (from house-info, or the "
                            "lot every PO prints when house-info gives none)")
    return problems


def header_problems(request_pages, header):
    """The job line carries exactly the house's address and lot numbers, every PO's job name is in
    the header, and the only document number printed is the one the commit will give."""
    text = normalise(" ".join(request_pages))
    head = text[:text.find("before tax")] if "before tax" in text else text
    problems, job = [], JOB_LINE.search(head)
    if header["job_numbers"] is not None:
        printed = sorted(re.findall(r"\d+", job.group(1))) if job else None
        if printed != sorted(header["job_numbers"]):
            problems.append(f"the job line reads '{job.group(1) if job else ''}'; house-info (and, when it gives no lot, the "
                            "lot every PO prints) gives the numbers "
                            + ", ".join(header["job_numbers"]))
    problems += job_text_problems(job.group(1) if job else "", header)
    if not header["job_names"] and header["job_numbers"] is None:
        problems.append("nothing to check the job line against: the POs give no job name and house-info "
                        "gives no address or lot. Fill in house-info.md in 01 intake")
    for name in header["job_names"]:
        if normalise(name) not in head:
            problems.append(f"the PO's job name {name} is not in the header. Check that PO is for this "
                            "house: a PO for another house comes out of intake (ask Sam), it never goes in the header")
    problems += measured_problems(head, header.get("measured"), "measured" in header)
    if header.get("practice") is False and "practice sample" in text:
        problems.append("the request says PRACTICE SAMPLE, but reference/contractor.md is a real contractor: "
                        "delete the badge line from request.html")
    problems += who_problems(head, header) + facts_problems(head, header)
    want = int(header["document"].split("-")[1])
    found = sorted({int(n) for n in DOCUMENT.findall(text)})
    if found != [want]:
        problems.append(f"the request prints {', '.join(f'VR-{n:04d}' for n in found) or 'no document number'}; "
                        f"this commit would number it {header['document']}. The number comes from the commit, "
                        "never typed by hand; if a request from this review is already numbered, a new one "
                        "needs a new review with Sam's yes")
    return problems
