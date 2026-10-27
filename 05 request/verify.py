"""The six request checks, run by script on the real PDF. Nothing the AI wrote is trusted.

1. Only approved rows, and all of them   2. Each difference matches   3. Tax per PO group
4. House totals                          5. Every proof document attached   6. Page count and footer

`expected` comes from money.expected_request(); `proof` names what must (and must not) be attached.
Each check returns one line: "N. Name: pass: <evidence>" or "N. Name: fail: <what is on the PDF,
and what was expected>". A request with any fail line is never numbered.
"""
import re
from decimal import Decimal

import pymupdf

FOOTER_TEXT = "Checked and approved by"
MONEY = re.compile(r"(\()?([+\-−])?\s?\$\s?([\d,]+\.\d\d)")


def normalise(text):
    """Lower case, one space between words, plain quotes: so a wrapped line still matches."""
    text = text.replace("’", "'").replace("‘", "'").replace("′", "'").replace("−", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def amounts(text):
    """Every dollar amount printed, signed: '-$170.00' and '($170.00)' are both -170.00."""
    found = []
    for m in MONEY.finditer(text):
        value = Decimal(m.group(3).replace(",", ""))
        found.append(-value if (m.group(1) or m.group(2) in ("-", "−")) else value)
    return found


def pdf_pages(path):
    """The text of every page, or None if the file is not a PDF that opens."""
    try:
        with pymupdf.open(path) as doc:
            if not doc.is_pdf or doc.page_count == 0:
                return None
            return [page.get_text() for page in doc]
    except Exception:
        return None


def split_request(pages):
    """The request runs from page 1 to the page with the sign-off footer; the proof follows."""
    for i, text in enumerate(pages):
        if FOOTER_TEXT in text:
            return pages[: i + 1], pages[i + 1:]
    return pages, []


def line(num, name, problems, evidence):
    if problems:
        return f"{num}. {name}: fail: " + "; ".join(problems)
    return f"{num}. {name}: pass: {evidence}"


def check_rows(request, expected):
    text = normalise(request)
    missing = [r["item"] for r in expected["rows_on"] if normalise(r["item"]) not in text]
    present = [item for item in expected["rows_off"] if normalise(item) in text]
    problems = [f"missing from the PDF: {m}" for m in missing]
    problems += [f"on the PDF but Sam chose it off: {p}" for p in present]
    return line(1, "Only approved rows, and all of them", problems,
                f"{len(expected['rows_on'])} approved row(s) printed, {len(expected['rows_off'])} left off")


def check_differences(request, expected):
    printed = amounts(request)
    problems = [f"{r['item']}: expected {r['difference']:+.2f}, not on the PDF"
                for r in expected["rows_on"] if r["difference"] not in printed]
    return line(2, "Each difference matches the variance", problems,
                ", ".join(f"{r['difference']:+.2f}" for r in expected["rows_on"]))


def check_tax(request, expected):
    printed = [abs(a) for a in amounts(request)]
    problems = []
    for po, g in expected["groups"].items():
        for label in ("tax", "total"):
            if abs(g[label]) not in printed:
                problems.append(f"{po} group {label}: expected ${g[label]:.2f}, not on the PDF")
    evidence = "; ".join(f"{po}: tax ${g['tax']:.2f}, total ${g['total']:.2f}" for po, g in expected["groups"].items())
    return line(3, "Tax per PO, from its own printed rate", problems, evidence)


def check_house(request, expected):
    printed = amounts(request)
    house = expected["house"]
    problems = [f"house {k}: expected ${house[k]:.2f}, not on the PDF" for k in ("before", "tax", "total")
                if house[k] not in printed and abs(house[k]) not in [abs(a) for a in printed]]
    return line(4, "House totals add up", problems,
                f"${house['before']:.2f} before tax + ${house['tax']:.2f} tax = ${house['total']:.2f}")


def check_proof(proof_pages, proof):
    text = normalise(" ".join(proof_pages))
    problems = []
    if not proof_pages:
        problems.append("no proof pages after the request")
    for name in proof["po_numbers"] + proof["epo_names"]:
        if normalise(name) not in text:
            problems.append(f"not attached: {name}")
    if proof["notes_marker"]:
        notes_in = normalise(proof["notes_marker"]) in text
        if proof["notes"] and not notes_in:
            problems.append("Sam said attach his site notes; they are not attached")
        if not proof["notes"] and notes_in:
            problems.append("Sam said not to attach his site notes; they are attached")
    evidence = (f"{len(proof['po_numbers'])} PO(s), {len(proof['epo_names'])} EPO(s), site notes "
                f"{'attached' if proof['notes'] else 'not attached (Sam said no)'}; {len(proof_pages)} proof page(s)")
    return line(5, "Every proof document attached", problems, evidence)


def check_pages(request_pages):
    first = request_pages[0] if request_pages else ""
    printed = re.search(r"page 1 of (\d+)", first)
    problems = []
    if FOOTER_TEXT not in request_pages[-1]:
        problems.append("no sign-off footer found")
    if not printed:
        problems.append("no 'page 1 of N' on page 1")
    elif int(printed.group(1)) != len(request_pages):
        problems.append(f"prints 'page 1 of {printed.group(1)}'; the request has {len(request_pages)} page(s)")
    return line(6, "Page count printed equals actual pages, footer on the last page", problems,
                f"prints 'page 1 of {len(request_pages)}', footer on page {len(request_pages)}")


def run_checks(pdf_path, expected, proof):
    """All six lines for one PDF. A file that is not a real PDF fails every check."""
    pages = pdf_pages(pdf_path)
    if pages is None:
        return [f"{n}. {name}: fail: {pdf_path.name} is not a PDF that opens" for n, name in
                enumerate(["Only approved rows", "Differences", "Tax", "House totals", "Proof", "Pages"], 1)]
    request_pages, proof_pages = split_request(pages)
    request = " ".join(request_pages)
    return [check_rows(request, expected), check_differences(request, expected), check_tax(request, expected),
            check_house(request, expected), check_proof(proof_pages, proof), check_pages(request_pages)]
