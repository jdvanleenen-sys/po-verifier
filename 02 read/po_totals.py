"""The POs read check: each row of the read-back's POs read table is set against its PO file in 01 intake.

The subtotal, each tax amount (by name) and the total written in the read-back must be the ones the
PO file prints. A tax copied wrong (PST $451.37 for the $225.69 the PO prints) would otherwise pass:
the grid's tax-total rule only checks that the read-back adds up with itself. Run by grid.py check,
beside po_lines. Only an HTML PO ("Subtotal: ... GST/HST Tax Total: ... PST Tax Total: ... Total:
...", as SupplyPro and BuildPro save them) can be read this way; a PO on a PDF is counted and named
for a check by eye, never passed.
"""
import re

import grid_read
import grid_rules as rules
import po_lines

SUBTOTAL = re.compile(r"\bsubtotal:", re.I)
TAX = re.compile(r"([A-Za-z][A-Za-z/]*)\s+Tax Total:\s*(-?\s*\$?\s*-?[\d,]+(?:\.\d+)?)", re.I)
TOTAL = re.compile(r"(?<!Tax )\bTotal:\s*(-?\s*\$?\s*-?[\d,]+(?:\.\d+)?)", re.I)
NAME = re.compile(r"\s*([A-Za-z][A-Za-z/ ]*?)\s*(?=[-$\d])")


def tax_key(name):
    return re.sub(r"\s+", "", name).upper()


def printed_totals(text):
    """{"subtotal", "taxes": {name: amount}, "total"} as the PO file prints them, or None."""
    m = SUBTOTAL.search(text)
    if not m:
        return None
    tail = text[m.end():m.end() + 400]
    sub = po_lines.numbers(tail)
    total = TOTAL.search(tail)
    if not sub or not total:
        return None
    taxes = {tax_key(n): po_lines.numbers(a)[0] for n, a in TAX.findall(tail[:total.start()])}
    return {"subtotal": sub[0], "taxes": taxes, "total": po_lines.numbers(total.group(1))[0]}


def written_taxes(cell):
    """{name: amount} from a read-back 'Tax lines' cell: 'GST/HST $0.00; PST $225.69'."""
    out = {}
    for part in cell.split(";"):
        name, amounts = NAME.match(part), po_lines.numbers(part)
        if name and amounts:
            out[tax_key(name.group(1))] = amounts[-1]
    return out


def money(value):
    return f"${rules.show(value)}" if value is not None else "nothing"


def tax_problems(where, printed, written):
    problems = []
    for name in sorted(set(printed) | set(written)):
        p, w = printed.get(name), written.get(name)
        if w is None and p:
            problems.append(f"{where}: the PO prints {name} {money(p)}, the read-back leaves it out")
        elif p is None and w is not None:
            problems.append(f"{where}: the PO prints no {name} tax, the read-back says {money(w)}")
        elif w is not None and p != w:
            problems.append(f"{where}: the PO prints {name} {money(p)}, the read-back says {money(w)}")
    return problems


def row_problems(r, docs):
    po = r.get("po number", "").strip()
    where = f"POs read row {po}"
    found = [printed_totals(text) for text, segs in docs if segs is not None and po and po in text]
    found = [f for f in found if f]
    if not found:
        return None
    p = found[0]
    problems = []
    for key in ("subtotal", "total"):
        w = rules.number(rules.cell(r, key))
        if w != p[key]:
            problems.append(f"{where}: the PO prints {key} {money(p[key])}, the read-back says {money(w)}")
    return problems + tax_problems(where, p["taxes"], written_taxes(rules.cell(r, "tax lines")))


def check(folder, read_back_text):
    """(problems, the PO numbers in POs read that could not be checked because no HTML PO in intake
    prints them). A PO number no file in intake prints at all, with no PDF to explain it, is refused."""
    if not folder.is_dir():
        return [f"POs read: no intake folder {folder.name} to check the totals against"], []
    files = po_lines.po_files(folder)
    docs = [po_lines.segments(p) for p in files]
    has_pdf = any(p.suffix.lower() == ".pdf" for p in files)
    problems, unchecked = [], []
    for r in grid_read.as_dicts(grid_read.under(read_back_text, "pos read")):
        found = row_problems(r, docs)
        if found is None:
            po = r.get("po number", "").strip()
            if has_pdf:
                unchecked.append(po)
            else:
                problems.append(f"POs read row {po}: no PO in 01 intake prints this ORDER # with its totals")
        else:
            problems += found
    return problems, unchecked
