"""Reading the request PDF's text: pages, dollar amounts with their sign, and the PO group
blocks with their labelled lines. Used by verify.py and row_checks.py."""
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


# The last line of every group block, exactly as reference/request-layout.html words it.
GROUP_END = re.compile(r"(?:epo requested for this po|credit back to the builder for this po|new po or epo requested)\s*"
                       + MONEY.pattern)


PO_HEADING = re.compile(r"\bpo ([a-z]+-\d+/\d+)(?!\S*:)")


NO_PO_HEADING = "no po work done"


SUBTOTAL = "difference before tax"


BOX_NOTE = re.compile(r"(?:\bpo ([a-z]+-\d+/\d+)|\bno po): " + MONEY.pattern)


COLUMN_HEADINGS = "difference why"


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


def shown(value):
    return "nothing" if value is None else f"${value:.2f}"
