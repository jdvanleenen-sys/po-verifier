"""The rules every read-back row and every PO is checked against, one cell per rule.

Code fills every cell it can work out exactly. A cell code cannot decide is left as "?" for the AI,
who answers it one rule (one column) at a time across every row. grid.py builds and checks the grid.

A cell is a status, a colon, and what was looked at, such as "pass: 7 x 60.00 = 420.00".
"""
import re
from decimal import Decimal, InvalidOperation

import prices

ASK = "?"
PASS, FAIL, NA, AT_RISK, ASK_SAM, NOT_COMPARABLE = (
    "pass", "fail", "n/a", "at risk", "ask Sam", "not comparable")
STATUSES = (PASS, FAIL, NA, AT_RISK, ASK_SAM, NOT_COMPARABLE)
NO_PO = "none"
SELECTION = re.compile(r"selection:\s*([0-9][0-9.]*(?:e[+\-]?\d+)?)", re.I)
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
SIZE_NUMBER = re.compile(r"(?:count\s+)?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)", re.I)
SIZE_UNIT = re.compile(r"\s*(?:'|(?:ft|feet|lf|sf|sq\.?\s?ft|ea|each)\b)", re.I)
NOT_A_REMARK = re.compile(r"(?:\d|x\s*\d|in\b|inch|to\b|or\b|and\b|plus\b|[+&\-'\"])", re.I)
MONEY = re.compile(r"\$\s*[\d,]+(?:\.\d+)?")
DOT_FOR_COMMA = re.compile(r"\d{1,3}\.\d{3}")
CONFIRMED = "sam confirmed"
TEN_TIMES = Decimal(10)

# Rule id: (question, filled by, the statuses the AI may answer with)
ROW_RULES = {
    "line-math": ("PO qty x unit price = line total, as printed", "code", ()),
    "po-read": ("The row's PO is in POs read, or a no-PO row is named under Extra items", "code", ()),
    "price": ("Item, unit and rate are exactly as on the price list snapshot", "code", ()),
    "unit": ("The unit printed on the PO is the price list unit (if not: At risk)", "code", ()),
    "selection": ("The selection printed under the line agrees with the PO qty (if not: At risk)", "code", ()),
    "measured": ("A size or count was read from Sam's notes", "code", ()),
    "po-line-match": ("The PO line, as printed, is this price list item", "AI", (PASS, ASK_SAM)),
    "note-match": ("Sam's note, read with the price list only, is this price list item", "AI", (PASS, ASK_SAM)),
    "line-notes": ("The notes under the line do not change what it covers (if they do: At risk)",
                   "code finds notes, AI answers", (PASS, AT_RISK)),
    "count": ("Sam's quantity can be set against the PO qty (not a lump sum or a part)", "AI",
              (PASS, NOT_COMPARABLE)),
}
PO_RULES = {
    "lines-subtotal": ("The line totals add up to the printed subtotal", "code", ()),
    "tax-total": ("Subtotal plus the tax lines equals the printed total", "code", ()),
    "once": ("The PO number appears once in POs read", "code", ()),
    "vendor": ("Every PO is to the same vendor", "code", ()),
    "address": ("The job address matches the address Sam gave", "AI", (PASS, FAIL)),
}


def number(cell):
    """A plain number as printed: 7, 2.75, $1,000.00 or 1.000000000000000e+000. None if not one.
    A comma counts only between thousands (prices.plain): 24,50 is not a number."""
    return prices.plain(cell)


def show(value):
    """A Decimal without trailing zeros or exponent: 3020, 2.75, 1."""
    return f"{value.normalize():f}" if value is not None else "?"


def cell(row, start):
    """The cell whose header starts with these words."""
    return next((v for k, v in row.items() if k.startswith(start)), "")


def po_of(row):
    return NO_PO if cell(row, "po number").strip().lower() in ("", NO_PO) else cell(row, "po number").strip()


def item_state(row):
    item = " ".join(row.get("price list item", "").split()).lower()
    if item.startswith(prices.PENDING):
        return "pending"
    return "unpriced" if item.startswith(prices.UNPRICED) or not item else "priced"


def size_slot(text):
    """The part of a "Sam measured" cell that holds his size or count: the ';' part after his first
    quoted phrase, or, without quotes, the second ';' part, as in "stringers; 34 ft"."""
    if '"' in text:
        start = text.index('"')
        end = text.find('"', start + 1)
        if end < 0:
            return None
        parts = text[end + 1:].split(";")
        return parts[1] if not parts[0].strip() and len(parts) > 1 else parts[0]
    parts = text.split(";")
    return parts[1] if len(parts) > 1 else None


def measured_text(row):
    """Sam's size or count as written, from the size slot (size_slot), or None.

    The slot must open with one plain number: optionally "count " before it, a unit after it
    (', ft, feet, LF, SF, sq ft, EA, each), then nothing, or a remark in words ("0 here, counted
    on /027", "3016, Sam confirmed"). Anything else is no size, so the grid asks Sam: feet and
    inches (13'6", 13 ft 6 in), a multiplier (124 ft x2), a range (10-12'), a number in words
    (ten), a pointer (see row 3), or a comma that is not between thousands (10,5).
    His words are the FIRST quoted phrase: a quoted name later in the cell, such as a source note
    '(photo, under "12 Sample Road", line 2)', must not move where the size is read from.
    """
    slot = (size_slot(cell(row, "sam measured")) or "").strip()
    found = SIZE_NUMBER.match(slot)
    if not found:
        return None
    rest = slot[found.end():]
    unit = SIZE_UNIT.match(rest)
    rest = rest[unit.end():] if unit else rest
    if rest and (rest[0] not in " ,	" or NOT_A_REMARK.match(rest.lstrip(" ,	"))):
        return None
    return found.group(1)


def measured_qty(row):
    text = measured_text(row)
    return Decimal(text.replace(",", "")) if text else None


def confirmed(row):
    """Sam was asked about this row's number and confirmed it; the read-back says so on the row."""
    return CONFIRMED in cell(row, "sam measured").lower()


def no_item_yet(row):
    state = item_state(row)
    if state == "priced":
        return None
    return f"{NA}: waiting on Sam's pick (see price)" if state == "pending" else f"{NA}: not on the price list"


def line_math(row, _):
    if po_of(row) == NO_PO:
        return f"{NA}: on no PO"
    qty, price, total = (number(cell(row, k)) for k in ("po qty", "unit price", "line total"))
    if None in (qty, price, total):
        return f"{FAIL}: PO qty, unit price or line total is not a number"
    sign = "=" if qty * price == total else "is not"
    status = PASS if sign == "=" else FAIL
    return f"{status}: {show(qty)} x {show(price)} {sign} {show(total)}"


def po_read(row, house):
    po, num = po_of(row), row.get("#", "").strip()
    if po != NO_PO:
        found = po in house["po_numbers"]
        return f"{PASS}: {po} is in POs read" if found else f"{FAIL}: {po} is not in POs read"
    if re.search(rf"\brow {re.escape(num)}\b", house["extras"], re.I):
        return f"{PASS}: on no PO, named under Extra items"
    return f"{FAIL}: on no PO, but row {num} is not named under Extra items"


def price(row, house):
    state = item_state(row)
    if state == "pending":
        return f"{ASK_SAM}: waiting on his pick one"
    if state == "unpriced":
        return f"{NA}: not on the price list; Sam's answer is in the warning table"
    problems = prices.check_price_row(row, house["prices"])
    if problems:
        return f"{FAIL}: " + "; ".join(p.split(": ", 1)[-1] for p in problems)
    return f"{PASS}: {row.get('unit', '').strip()} at {row.get('rate', '').strip()} on the snapshot"


def unit(row, _):
    if po_of(row) == NO_PO:
        return f"{NA}: on no PO"
    waiting = no_item_yet(row)
    if waiting:
        return waiting
    printed = cell(row, "unit as printed").split("(")[0].strip()
    listed = row.get("unit", "").strip()
    if printed == listed:
        return f"{PASS}: printed {printed}, price list {listed}"
    return f"{AT_RISK}: printed {printed or 'blank'} on a line the price list prices per {listed}"


def selection(row, _):
    if po_of(row) == NO_PO:
        return f"{NA}: on no PO"
    found = SELECTION.search(cell(row, "special option info"))
    if not found:
        return f"{NA}: no selection printed"
    chosen, qty = number(found.group(1)), number(cell(row, "po qty"))
    if chosen is not None and chosen == qty:
        return f"{PASS}: selection {show(chosen)}, qty {show(qty)}"
    return f"{AT_RISK}: qty {show(qty)}, selection {show(chosen)}; both recorded"


def measured(row, _):
    if item_state(row) == "unpriced":
        return f"{NA}: not on the price list, so nothing is set against it"
    qty = measured_qty(row)
    if qty is None:
        return f"{ASK_SAM}: no size or count read from his notes"
    doubt = None if confirmed(row) else size_doubt(row, qty)
    return f"{ASK_SAM}: {doubt}; once he answers, write 'Sam confirmed' on the row" if doubt else f"{PASS}: {show(qty)}"


def size_doubt(row, qty):
    """Why a measured number needs Sam before it is priced, or None. Each of these has cost real money."""
    if DOT_FOR_COMMA.fullmatch(measured_text(row)):
        return f"'{measured_text(row)}' may be a thousands number written with a dot for a comma"
    po_qty = number(cell(row, "po qty")) if po_of(row) != NO_PO else None
    if not po_qty:
        return None
    if qty == 0:
        return f"0 measured against a PO qty of {show(po_qty)}: the whole line becomes a credit"
    if qty >= po_qty * TEN_TIMES or qty * TEN_TIMES <= po_qty:
        return f"{show(qty)} is ten times or more off the PO qty of {show(po_qty)}"
    return None


def po_line_match(row, _):
    if po_of(row) == NO_PO:
        return f"{NA}: on no PO"
    return no_item_yet(row) or ASK


def note_match(row, _):
    if measured_qty(row) is None:
        return f"{NA}: nothing measured (see measured)"
    return no_item_yet(row) or ASK


def line_notes(row, _):
    if po_of(row) == NO_PO:
        return f"{NA}: on no PO"
    return ASK if "notes:" in cell(row, "special option info").lower() else f"{NA}: no notes under the line"


def count(row, house):
    if po_of(row) == NO_PO:
        return f"{NA}: on no PO, set against 0"
    twin = None if confirmed(row) else ordered_twice(row, house.get("rows", []))
    if twin:
        return (f"{ASK_SAM}: the same item, qty and price is also on PO {twin}; ordered twice? "
                "Once he answers, write 'Sam confirmed' on the row")
    return no_item_yet(row) or ASK


def ordered_twice(row, rows):
    """Another PO carrying this row's item at the same qty and price, or None."""
    key = lambda r: (" ".join(r.get("price list item", "").split()).lower(),
                     number(cell(r, "po qty")), number(cell(r, "unit price")))
    for other in rows:
        if po_of(other) not in (NO_PO, po_of(row)) and key(other) == key(row) and key(row)[1]:
            return po_of(other)
    return None


ROW_CHECKS = {"line-math": line_math, "po-read": po_read, "price": price, "unit": unit,
              "selection": selection, "measured": measured, "po-line-match": po_line_match,
              "note-match": note_match, "line-notes": line_notes, "count": count}


def money_sum(text):
    return sum((number(m.group(0)) for m in MONEY.finditer(text or "")), Decimal(0))


def lines_subtotal(po_row, house):
    po = po_row["po number"].strip()
    totals = [number(cell(r, "line total")) for r in house["rows"] if po_of(r) == po]
    subtotal = number(cell(po_row, "subtotal"))
    if not totals or None in totals or subtotal is None:
        return f"{FAIL}: no line totals or no subtotal read for {po}"
    added = sum(totals, Decimal(0))
    shown = " + ".join(show(t) for t in totals)
    status, sign = (PASS, "=") if added == subtotal else (FAIL, "is not")
    return f"{status}: {shown} {sign} {show(subtotal)}"


def tax_total(po_row, _):
    subtotal, total = number(cell(po_row, "subtotal")), number(cell(po_row, "total"))
    if subtotal is None or total is None:
        return f"{FAIL}: no subtotal or total read"
    tax = money_sum(cell(po_row, "tax lines"))
    status, sign = (PASS, "=") if subtotal + tax == total else (FAIL, "is not")
    return f"{status}: {show(subtotal)} + {show(tax)} {sign} {show(total)}"


def once(po_row, house):
    times = house["po_numbers"].count(po_row["po number"].strip())
    return f"{PASS}: listed once" if times == 1 else f"{FAIL}: listed {times} times; stop and ask Sam"


def vendor(po_row, house):
    names = {" ".join(cell(r, "vendor").split()) for r in house["pos"]}
    return f"{PASS}: every PO is to {names.pop()}" if len(names) == 1 else f"{FAIL}: vendors differ"


def address(_, __):
    return ASK


PO_CHECKS = {"lines-subtotal": lines_subtotal, "tax-total": tax_total, "once": once,
             "vendor": vendor, "address": address}
