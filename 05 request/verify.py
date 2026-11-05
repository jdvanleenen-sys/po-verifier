"""The six request checks, run by script on the real PDF. Nothing the AI wrote is trusted.

1. Only approved rows, and all of them   2. Each row's figures, on that row   3. Each PO group's sums
4. House totals                          5. Every proof document attached   6. Page count and footer

`expected` comes from money.expected_request(); `proof` names what must (and must not) be attached.
Each check returns one line: "N. Name: pass: <evidence>" or "N. Name: fail: <what is on the PDF,
and what was expected>". A request with any fail line is never numbered.
"""
import re
from decimal import Decimal

import pymupdf

FOOTER_TEXT = "Checked and approved by"
MONEY = re.compile(r"(\()?([+\-−])?\s?\$\s?((?:\d{1,3}(?:,\d{3})+|\d+)\.\d\d)(?!\d)")
QTY = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


def normalise(text):
    """Lower case, one space between words, plain quotes: so a wrapped line still matches."""
    text = text.replace("’", "'").replace("‘", "'").replace("′", "'").replace("−", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def marked_amounts(text, spans=False):
    """Every dollar amount printed, as (value, printed with a sign), plus its (start, end) if spans.
    '-$170.00' and '($170.00)' are both -170.00, signed; '+$300.00' is signed; '$60.00' is not."""
    found = []
    for m in MONEY.finditer(text):
        value = Decimal(m.group(3).replace(",", ""))
        negative = bool(m.group(1)) or m.group(2) in ("-", "−")
        item = (-value if negative else value, bool(m.group(1) or m.group(2)))
        found.append(item + (m.span(),) if spans else item)
    return found


def amounts(text):
    """Every dollar amount printed, signed: '-$170.00' and '($170.00)' are both -170.00."""
    return [value for value, _ in marked_amounts(text)]


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


# The last line of every group block, exactly as reference/request-layout.html words it.
GROUP_END = re.compile(r"(?:epo requested for this po|credit back to the builder for this po|new po or epo requested)\s*"
                       + MONEY.pattern)
PO_HEADING = re.compile(r"\bpo ([a-z]+-\d+/\d+)(?!\S*:)")
NO_PO_HEADING = "no po work done"
SUBTOTAL = "difference before tax"
COLUMN_HEADINGS = "difference why"
# The main box's label: what is owed to the trade, or, when the house nets to a credit, what goes back.
OWED_TOTAL, CREDIT_TOTAL = "total requested", "total credit to the builder"


def first_amount_after(text, label):
    """The signed amount printed right after a label, or None if the label or amount is missing."""
    at = text.find(label)
    if at < 0:
        return None
    found = amounts(text[at + len(label):])
    return found[0] if found else None


def group_key(block):
    """The heading a group block starts under: its PO number, or "none" for the no-PO block.
    The heading is the first one in the block; a PO named later, in a row's wording, is not it."""
    first_po = PO_HEADING.search(block)
    no_po = block.find(NO_PO_HEADING)
    if no_po >= 0 and (first_po is None or no_po < first_po.start()):
        return "none", no_po
    return (first_po.group(1), first_po.start()) if first_po else (None, 0)


def group_blocks(request):
    """Each group block on the request, by its heading: ({po: (block from its heading, end line)},
    [each PO whose heading is printed more than once])."""
    text, out, twice, start = normalise(request), {}, [], 0
    for end in GROUP_END.finditer(text):
        block, start = text[start:end.start()], end.end()
        key, at = group_key(block)
        if key is None:
            continue
        if key in out:
            twice.append(key)
        out[key] = (block[at:], end.group(0))
    return out, twice


def printed_groups(request):
    """Each group block on the request, by its heading: {po: (difference before tax, tax, total)}."""
    out = {}
    for key, (block, end_line) in group_blocks(request)[0].items():
        tail = block[block.find(SUBTOTAL):] if SUBTOTAL in block else ""
        values, total = amounts(tail), amounts(end_line)
        out[key] = (values[0] if values else None, values[1] if len(values) > 1 else None,
                    total[0] if total else None)
    return out


def row_starts(block, items):
    """Where each item's row starts in its group block: after the column headings, before the
    subtotal. A name that is part of a longer item's name is not found inside that longer name."""
    head = block.find(COLUMN_HEADINGS)
    first = head + len(COLUMN_HEADINGS) if head >= 0 else 0
    stop = block.find(SUBTOTAL) if SUBTOTAL in block else len(block)
    taken, starts = [], {}
    for name in sorted({normalise(i) for i in items}, key=len, reverse=True):
        at = block.find(name, first)
        while 0 <= at < stop and any(a <= at < b for a, b in taken):
            at = block.find(name, at + 1)
        if 0 <= at < stop:
            starts[name] = at
            taken.append((at, at + len(name)))
    return starts, stop


def read_row(segment):
    """One printed row after its item name: (plain amounts before the difference, the difference,
    the text between each pair of those plain amounts). The difference is the first amount printed
    with a sign. The plain amounts before it are the agreed rate, the PO rate (blank on a no-PO row),
    the PO amount and the measured value; the PO qty sits after the rate, the measured qty before
    the measured value."""
    plain, spans = [], []
    for value, signed, span in marked_amounts(segment, spans=True):
        if signed:
            return plain, value, gaps(segment, spans)
        plain.append(value)
        spans.append(span)
    return plain, None, gaps(segment, spans)


def gaps(text, spans):
    return [text[a[1]:b[0]] for a, b in zip(spans, spans[1:])]


def quantity(gap):
    """The one number printed in a gap between two amounts: '12', '2,615.5'; blank reads as 0."""
    found = QTY.findall(gap)
    if not found:
        return Decimal(0)
    return Decimal(found[0].replace(",", "")) if len(found) == 1 else None


def quantity_problems(where, row, between):
    if "po_qty" not in row:
        return []
    out = []
    for label, want, got in (("PO qty", row["po_qty"], quantity(between[0]) if between else None),
                             ("measured qty", row["measured_qty"], quantity(between[-1]) if between else None)):
        if got != want:
            out.append(f"{where}: {label} expected {want}, its row shows {'nothing clear' if got is None else got}")
    return out


def row_problems(row, plain, difference, between=()):
    """Each figure on one printed row against the one worked out from Sam's read-back."""
    where, out = f"{row['item']} ({row['po']})", []
    if difference != row["difference"]:
        out.append(f"{where}: difference expected {row['difference']:+.2f}, its row shows "
                   + ("no signed amount" if difference is None else f"{difference:+.2f}"))
    if "po_amount" not in row:
        return out
    full = len(plain) >= 3
    for label, want, got in (("agreed rate", row["rate"], plain[0] if plain else None),
                             ("PO amount", row["po_amount"], plain[-2] if full else None),
                             ("measured value", row["measured_value"], plain[-1] if full else None)):
        if got != want:
            out.append(f"{where}: {label} expected ${want:.2f}, its row shows {shown(got)}")
    return out + (quantity_problems(where, row, between) if full else [])


def rows_by_po(rows):
    out = {}
    for row in rows:
        out.setdefault(row["po"].lower(), []).append(row)
    return out


def block_problems(po, rows, block):
    """One PO block: each approved row read from its own row, and no other row in the block.
    Every row prints its difference with a sign, so the block holds one signed amount per row."""
    starts, stop = row_starts(block, [r["item"] for r in rows])
    ends, problems = sorted(starts.values()) + [stop], []
    for row in rows:
        name = normalise(row["item"])
        if name not in starts:
            problems.append(f"{row['item']} ({row['po']}): no row for it in its PO's block")
            continue
        at = starts[name]
        problems += row_problems(row, *read_row(block[at + len(name):next(e for e in ends if e > at)]))
    head = block.find(COLUMN_HEADINGS)
    printed = sum(1 for _, signed in marked_amounts(block[max(head, 0):stop]) if signed)
    if printed != len(rows):
        problems.append(f"PO {rows[0]['po']}: its block prints {printed} row difference(s); Sam approved {len(rows)} row(s)")
    return problems


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


def shown(value):
    return "nothing" if value is None else f"${value:.2f}"


def check_tax(request, expected):
    """Each PO's tax and requested total, read from that PO's own block, sign included."""
    found, problems = printed_groups(request), []
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
    return line(4, "House totals add up", problems,
                f"${house['before']:.2f} before tax + ${house['tax']:.2f} tax = ${house['total']:.2f}")


def check_proof(proof_pages, proof):
    """Every PO and EPO attached; each notes page Sam named attached; each one he left out absent.
    A notes page is found by its file name, printed as the heading of its proof page."""
    text = normalise(" ".join(proof_pages))
    problems = []
    if not proof_pages:
        problems.append("no proof pages after the request")
    for name in proof["po_numbers"] + proof["epo_names"]:
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
