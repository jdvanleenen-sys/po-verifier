"""The six request checks, run by script on the real PDF. Nothing the AI wrote is trusted.

1. Only approved rows and amounts       2. Each row's figures, on that row   3. Each PO group's sums
4. House totals                          5. Every proof document attached   6. Page count and footer

`expected` comes from money.expected_request(); `proof` names what must (and must not) be attached.
Each check returns one line: "N. Name: pass: <evidence>" or "N. Name: fail: <what is on the PDF,
and what was expected>". A request with any fail line is never numbered.
"""
import re
from decimal import Decimal

from request_text import (  # noqa: F401  (pdf_pages, split_request, normalise: used by callers)
    BOX_NOTE, FOOTER_TEXT, amounts, first_amount_after, group_blocks, normalise, pdf_pages,
    SUBTOTAL, printed_groups, shown, split_request)
from header_checks import header_problems
from row_checks import block_problems, rows_by_po

D0 = Decimal(0)


def line(num, name, problems, evidence):
    if problems:
        return f"{num}. {name}: fail: " + "; ".join(problems)
    return f"{num}. {name}: pass: {evidence}"


def without_names(text, names):
    """The text with each name blanked out, longest first, so a shorter name is not found inside it."""
    for name in sorted({normalise(n) for n in names}, key=len, reverse=True):
        text = text.replace(name, " ")
    return text


def names_holding(item, rows_on):
    """The approved items whose names hold this one ("8' doors and trim" holds "8' doors")."""
    return [r["item"] for r in rows_on if normalise(item) in normalise(r["item"])]


def known_amounts(expected):
    """Every dollar figure the records give for this request, without its sign (signs are checked
    on their own lines): row figures, group and house sums, PO rates and EPO totals, and $0.00."""
    figures = {D0}
    for r in expected["rows_on"]:
        figures |= {r[k] for k in ("rate", "po_amount", "measured_value", "difference") if k in r}
    for g in expected["groups"].values():
        figures |= set(g.values())
    figures |= set(expected.get("house", {}).values()) | set(expected.get("other_amounts", []))
    return {abs(v) for v in figures}


def stray_amounts(request, expected):
    """Dollar amounts printed on the request that no record gives (an invented figure, a row with
    no sign). Run only on an expected request built by money.py, which lists the other amounts."""
    if "other_amounts" not in expected:
        return []
    known = known_amounts(expected)
    return [f"${v:,.2f} is printed, but no record gives it" for v in amounts(request) if abs(v) not in known]


def check_rows(request, expected):
    text = normalise(request)
    missing = [r["item"] for r in expected["rows_on"] if normalise(r["item"]) not in text]
    present = [item for item in expected["rows_off"]
               if normalise(item) in without_names(text, names_holding(item, expected["rows_on"]))]
    problems = [f"missing from the PDF: {m}" for m in missing]
    problems += [f"on the PDF but Sam chose it off: {p}" for p in present]
    problems += stray_amounts(request, expected)
    return line(1, "Only approved rows and amounts, and all of them", problems,
                f"{len(expected['rows_on'])} approved row(s) printed, {len(expected['rows_off'])} left off")


# The main box's label: what is owed to the trade, or, when the house nets to a credit, what goes back.
OWED_TOTAL, CREDIT_TOTAL = "total requested", "total credit to the builder"


def check_differences(request, expected):
    """Each approved row's figures, read from that row inside its own PO's block, never from
    anywhere else on the page; no block or row the records do not give."""
    blocks, twice = group_blocks(request)
    problems = [f"PO {po} has more than one group block" for po in twice]
    by_po = rows_by_po(expected["rows_on"])
    problems += [f"PO {po.upper()}: a group block is printed, but Sam approved no row on it"
                 for po in blocks if po not in by_po]
    for po, rows in by_po.items():
        if po not in blocks:
            problems += [f"{r['item']} ({r['po']}): its PO has no group block on the PDF" for r in rows]
            continue
        problems += block_problems(po, rows, blocks[po][0])
    return line(2, "Each row's figures match the variance, on that row", problems,
                ", ".join(f"{r['item']} {r['difference']:+.2f}" for r in expected["rows_on"]))


def end_label(po, total):
    """How a group's last line must start: the no-PO group, a PO that nets to a credit, or an EPO."""
    if po == "none":
        return "new po or epo requested"
    return "credit back to the builder for this po" if total < 0 else "epo requested for this po"


PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s?%")


def group_name(key):
    """A group as the request names it: its PO number, or "No PO"."""
    return "No PO" if key == "none" else key.upper()


def percents(text):
    return [Decimal(p) for p in PERCENT.findall(text)]


def rate_problems(blocks, expected):
    """The percentages on a group's tax lines add up to that PO's own rate (5% for GST alone)."""
    problems = []
    for key, (block, _) in blocks.items():
        rate = next((r for po, r in expected.get("rates", {}).items() if po.lower() == key), None)
        printed = percents(block[block.find(SUBTOTAL):]) if SUBTOTAL in block else []
        if rate is not None and sum(printed, D0) != rate * 100:
            problems.append(f"{group_name(key)}: its tax line prints {' + '.join(f'{p}%' for p in printed) or 'no rate'}; "
                            f"the PO's rate is {(rate * 100).normalize():f}%")
    return problems


def check_tax(request, expected):
    """Each PO's subtotal, tax and total, read from that PO's own block, sign included, and its
    last line worded by what the group is."""
    found, problems = printed_groups(request), []
    problems += rate_problems(group_blocks(request)[0], expected)
    for key, (_, line_text) in group_blocks(request)[0].items():
        group = next((g for po, g in expected["groups"].items() if po.lower() == key), None)
        if group and not line_text.startswith(end_label(key, group["total"])):
            problems.append(f"{group_name(key)}: its last line reads '{line_text}'; it must start "
                            f"'{end_label(key, group['total'])}'")
    for po, g in expected["groups"].items():
        got = found.get(po.lower())
        if got is None:
            problems.append(f"{po}: no group block on the PDF")
            continue
        for label, value in (("before", got[0]), ("tax", got[1]), ("total", got[2])):
            if value != g[label]:
                problems.append(f"{po} group {label}: expected ${g[label]:.2f}, the PDF shows {shown(value)}")
    evidence = "; ".join(f"{po}: before tax ${g['before']:.2f}, tax ${g['tax']:.2f}, total ${g['total']:.2f}"
                         for po, g in expected["groups"].items())
    return line(3, "Subtotal, tax and total per PO, from its own block", problems, evidence)


def box_note_problems(text, expected):
    """The main box's note names each group's total ("PO <number>: $315.00", "No PO: $705.60");
    each must be that group's own total."""
    totals = {po.lower(): g["total"] for po, g in expected["groups"].items()}
    problems = []
    for m in BOX_NOTE.finditer(text):
        key = m.group(1) or "none"
        value = amounts(m.group(0))[0]
        if key not in totals:
            problems.append(f"the box note names {key.upper()}, which has no group")
        elif value != totals[key]:
            problems.append(f"the box note gives {'No PO' if key == 'none' else key.upper()} "
                            f"{shown(value)}; its group total is {shown(totals[key])}")
    return problems


def box_text_problems(text, expected):
    """The boxes' own notes: the item count matches the approved rows ("2 items: 1 on a PO, 1 on no
    PO", the split only where it is written that way), and every percentage in the tax box is one a
    group's tax line prints."""
    start, end = text.find("before tax"), text.find(OWED_TOTAL if OWED_TOTAL in text else CREDIT_TOTAL)
    if start < 0 or end < start:
        return []
    box, rows, problems = text[start:end], expected.get("rows_on"), []
    on_po = sum(1 for r in rows or [] if r["po"] != "none")
    counts = [] if rows is None else [(r"(\d+) items?\b", len(rows), "items"),
                                      (r"(\d+) on (?:a )?po\b", on_po, "on a PO"),
                                      (r"(\d+) on no po\b", len(rows) - on_po, "on no PO")]
    for pattern, want, what in counts:
        m = re.search(pattern, box)
        if m and int(m.group(1)) != want:
            problems.append(f"the before-tax box says {m.group(1)} {what}; Sam approved {want}")
    lines = [p for block, _ in group_blocks(text)[0].values() for p in percents(block[block.find(SUBTOTAL):])]
    problems += [f"the tax box prints {p}%, which no group's tax line prints" for p in percents(box) if p not in lines]
    return problems


def check_house(request, expected):
    """The three boxes at the top, each read from its own label, in order, sign included."""
    text, house, problems, at = normalise(request), expected["house"], [], 0
    total_label = CREDIT_TOTAL if house["total"] < 0 else OWED_TOTAL
    for key, label in (("before", "before tax"), ("tax", "tax"), ("total", total_label)):
        index = text.find(label, at)
        value = first_amount_after(text[index:], label) if index >= 0 else None
        at = index + len(label) if index >= 0 else at
        if value != house[key]:
            problems.append(f"house {key} ('{label}' box): expected ${house[key]:.2f}, the PDF shows {shown(value)}")
    problems += box_note_problems(text, expected) + box_text_problems(text, expected)
    return line(4, "House totals add up", problems,
                f"${house['before']:.2f} before tax + ${house['tax']:.2f} tax = ${house['total']:.2f}")


def check_proof(proof_pages, proof):
    """Every PO and EPO attached; each notes page Sam named attached; each one he left out absent.
    A notes page is found by its file name, printed as the heading of its proof page. A PO counts
    as attached only from a page of its own: its number on an EPO page or a notes page does not count."""
    pages = [normalise(p) for p in proof_pages]
    text = " ".join(pages)
    others = [normalise(n) for n in proof["epo_names"] + proof["notes_attached"] + proof["notes_left_out"]]
    po_pages = [p for p in pages if not any(n in p for n in others)]
    problems = []
    if not proof_pages:
        problems.append("no proof pages after the request")
    for name in proof["po_numbers"]:
        if not any(normalise(name) in p for p in po_pages):
            problems.append(f"not attached: {name}" + (" (its number is only on an EPO or notes page)"
                                                       if normalise(name) in text else ""))
    for name in proof["epo_names"]:
        if normalise(name) not in text:
            problems.append(f"not attached: {name}")
    for name in proof["notes_attached"]:
        if normalise(name) not in text:
            problems.append(f"Sam said attach {name}; it is not attached")
    for name in proof["notes_left_out"]:
        if normalise(name) in text:
            problems.append(f"Sam left {name} out; it is attached")
    notes = ", ".join(proof["notes_attached"]) or "none (Sam said no)"
    evidence = (f"{len(proof['po_numbers'])} PO(s), {len(proof['epo_names'])} EPO(s), site notes: {notes}; "
                f"{len(proof_pages)} proof page(s)")
    return line(5, "Every proof document attached", problems, evidence)


def check_pages(request_pages, header=None):
    """Page count and footer; with a header spec from build_request, the job and document number too."""
    first = request_pages[0] if request_pages else ""
    printed = re.search(r"page 1 of (\d+)", first)
    problems = header_problems(request_pages, header) if header else []
    if FOOTER_TEXT not in request_pages[-1]:
        problems.append("no sign-off footer found")
    if not printed:
        problems.append("no 'page 1 of N' on page 1")
    elif int(printed.group(1)) != len(request_pages):
        problems.append(f"prints 'page 1 of {printed.group(1)}'; the request has {len(request_pages)} page(s)")
    evidence = f"prints 'page 1 of {len(request_pages)}', footer on page {len(request_pages)}"
    if header:
        evidence = f"{header['document']}, job {', '.join(header['job_names']) or '(no PO job name)'}; " + evidence
    return line(6, "Job, document number and page count printed right, footer on the last page", problems, evidence)


def run_checks(pdf_path, expected, proof, header=None):
    """All six lines for one PDF. A file that is not a real PDF fails every check."""
    pages = pdf_pages(pdf_path)
    if pages is None:
        return [f"{n}. {name}: fail: {pdf_path.name} is not a PDF that opens" for n, name in
                enumerate(["Only approved rows", "Differences", "Tax", "House totals", "Proof", "Pages"], 1)]
    request_pages, proof_pages = split_request(pages)
    request = " ".join(request_pages)
    return [check_rows(request, expected), check_differences(request, expected), check_tax(request, expected),
            check_house(request, expected), check_proof(proof_pages, proof), check_pages(request_pages, header)]
