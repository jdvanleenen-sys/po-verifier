"""The po-line rule: every read-back row on a PO is set against that PO's own file in 01 intake.

The row's PO qty, unit price and line total must all be printed on the PO line that carries its
description. A row whose numbers were read off another line (16 x 40.00 put on the doors line, both
$40 lines, so the subtotal still adds up) is refused. Run by grid.py check. Only an HTML PO (one table
row per PO line, as SupplyPro and BuildPro save them) can be read this way; rows on a PDF PO are
counted and named as not checked, never passed.
"""
import html
import re
from decimal import Decimal, InvalidOperation

import grid_read
import grid_rules as rules

NUM = re.compile(r"(-?)\s*\$?\s*(-?)(\d[\d,]*(?:\.\d+)?)")
ROW = re.compile(r"<tr\b.*?</tr>", re.S | re.I)
DASHES = re.compile(r"\s*[-‐-―]\s*")


def flat(markup):
    """Text with tags dropped, entities read and white space made single."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def norm(text):
    """For matching a description: case, dashes, spaces and a trailing ':' made alike."""
    return DASHES.sub("-", " ".join(html.unescape(text).split())).lower().rstrip(" :")


def numbers(text):
    """Every number printed in a piece of text, in order, signed: '$-1500.00' gives -1500.00."""
    out = []
    for m in NUM.finditer(text):
        try:
            value = Decimal(m.group(3).replace(",", ""))
        except InvalidOperation:
            continue
        out.append(-value if "-" in (m.group(1), m.group(2)) else value)
    return out


def segments(path):
    """(the file's whole text, its table rows) for an HTML PO. A PDF has no table rows to read, so it
    gives (its name, None): its rows are counted as not checked, never passed."""
    if path.suffix.lower() == ".pdf":
        return path.name, None
    raw = path.read_bytes().decode("utf-8", errors="replace")
    return flat(raw), [flat(tr) for tr in ROW.findall(raw)]


def po_files(folder):
    return [p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in (".html", ".htm", ".pdf")]


def show(value):
    return rules.show(value) if value is not None else "?"


def row_problem(r, docs):
    """Why this row's numbers are not on its PO line, or None."""
    po, num = rules.po_of(r), r.get("#", "").strip()
    line = norm(rules.cell(r, "line as printed"))
    want = [rules.number(rules.cell(r, k)) for k in ("po qty", "unit price", "line total")]
    if not line or None in want:
        return None if line else f"row {num}, po-line: fail: no line as printed to look for on PO {po}"
    found = [seg for text, segs in docs if segs and po in text for seg in segs if line in norm(seg)]
    said = f"{show(want[0])} x {show(want[1])} = {show(want[2])}"
    if not found:
        return f"row {num}, po-line: fail: PO {po} in 01 intake prints no line '{rules.cell(r, 'line as printed')}'"
    if any(all(w in numbers(seg) for w in want) for seg in found):
        return None
    printed = numbers(found[0])[-3:]
    shown = f"{show(printed[0])} x {show(printed[1])} = {show(printed[2])}" if len(printed) == 3 else "other numbers"
    return (f"row {num}, po-line: fail: the PO prints {shown} on '{rules.cell(r, 'line as printed')}', not {said}. "
            "Read the row again from that PO line")


def check(folder, read_back_text):
    """(every read-back row on an HTML PO whose qty, unit price and line total are not on its PO
    line, the number of rows on a PO that could not be checked because no HTML PO is in intake)."""
    if not folder.is_dir():
        return [f"po-line: no intake folder {folder.name} to check the rows against"], 0
    docs = [segments(p) for p in po_files(folder)]
    rows = [r for r in grid_read.as_dicts(grid_read.under(read_back_text, "rows")) if rules.po_of(r) != rules.NO_PO]
    html_pos = " ".join(text for text, segs in docs if segs is not None)
    checked = [r for r in rows if rules.po_of(r) in html_pos]
    found = (row_problem(r, docs) for r in checked)
    return [p for p in found if p], len(rows) - len(checked)
