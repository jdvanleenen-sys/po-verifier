"""Check 2's row reading: each approved row found in its own PO block and read cell by cell,
and no row in a block that Sam did not approve."""
import re
from decimal import Decimal

from request_text import COLUMN_HEADINGS, QTY, SUBTOTAL, marked_amounts, normalise, shown


# What follows an item's name on its own row: the unit, the agreed rate, then a quantity.
ROW_SHAPE = re.compile(r"\$\s?[\d,]+\.\d\d\s+\d[\d,.]*\s+[(+\-−]?\$")


ROW_CELLS = re.compile(r"\s*\S+\s+\$\s?[\d,]+\.\d\d\s+\d")


def row_starts(block, items):
    """Where each item's row starts in its group block: after the column headings, before the
    subtotal. A name that is part of a longer item's name is not found inside that longer name.
    A name that a row's why mentions is passed over for the place where the row's cells follow it."""
    head = block.find(COLUMN_HEADINGS)
    first = head + len(COLUMN_HEADINGS) if head >= 0 else 0
    stop = block.find(SUBTOTAL) if SUBTOTAL in block else len(block)
    taken, starts = [], {}
    for name in sorted({normalise(i) for i in items}, key=len, reverse=True):
        free, at = [], block.find(name, first)
        while 0 <= at < stop:
            if not any(a <= at < b for a, b in taken):
                free.append(at)
            at = block.find(name, at + 1)
        rows = [a for a in free if ROW_CELLS.match(block, a + len(name))]
        if rows or free:
            starts[name] = (rows or free)[0]
            taken.append((starts[name], starts[name] + len(name)))
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


def difference_end(segment):
    """Where a row's cells end: just after its first signed amount (its difference)."""
    for _, signed, span in marked_amounts(segment, spans=True):
        if signed:
            return span[1]
    return len(segment)


def stray_rows(po, block, first, stop, covered):
    """Anything shaped like a row (an amount, a quantity, an amount) outside the approved rows'
    own cells: a row Sam never saw, even one printed without a sign."""
    edges = [first] + [x for span in sorted(covered) for x in span] + [stop]
    outside = [block[a:b] for a, b in zip(edges[::2], edges[1::2])]
    if any(ROW_SHAPE.search(piece) for piece in outside):
        return [f"PO {po}: its block prints a row that is not one Sam approved"]
    return []


def block_problems(po, rows, block):
    """One PO block: each approved row read from its own row, and no other row in the block.
    Every row prints its difference with a sign, so the block holds one signed amount per row."""
    starts, stop = row_starts(block, [r["item"] for r in rows])
    ends, problems, covered = sorted(starts.values()) + [stop], [], []
    for row in rows:
        name = normalise(row["item"])
        if name not in starts:
            problems.append(f"{row['item']} ({row['po']}): no row for it in its PO's block")
            continue
        at = starts[name]
        segment = block[at + len(name):next(e for e in ends if e > at)]
        covered.append((at, at + len(name) + difference_end(segment)))
        problems += row_problems(row, *read_row(segment))
    head = block.find(COLUMN_HEADINGS)
    first = head + len(COLUMN_HEADINGS) if head >= 0 else 0
    problems += stray_rows(rows[0]["po"], block, first, stop, covered)
    printed = sum(1 for _, signed in marked_amounts(block[max(head, 0):stop]) if signed)
    if printed != len(rows):
        problems.append(f"PO {rows[0]['po']}: its block prints {printed} row difference(s); Sam approved {len(rows)} row(s)")
    return problems
