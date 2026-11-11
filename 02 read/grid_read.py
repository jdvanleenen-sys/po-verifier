"""Reading a read-back for the rule grid, and writing the grid code fills in.

Used by grid.py (build) and grid_check.py (check). See grid.py for how the grid is used.
"""
import hashlib
import re

import grid_rules as rules
import prices

HASHED = ("pos read", "rows", "extra items")


def sections(text):
    """Every '## heading' and the lines under it, keyed by the heading in lower case."""
    found, heading = {}, ""
    for line in text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
            found.setdefault(heading, [])
        else:
            found.setdefault(heading, []).append(line)
    return found


def under(text, start):
    """The lines under the first heading that starts with these words."""
    return next((lines for h, lines in sections(text).items() if h.startswith(start)), [])


def table(lines):
    """A Markdown table as (header, rows of cells). Header cells in lower case."""
    header, rows = None, []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
        elif not all(set(c) <= set("-: ") for c in cells):
            rows.append(cells)
    return header or [], rows


def as_dicts(lines):
    header, rows = table(lines)
    return [dict(zip(header, r)) for r in rows]


def tables_hash(read_back_text):
    """A fingerprint of what the code cells and the AI's answers were worked from."""
    parts = []
    for start in HASHED:
        parts += [" ".join(l.split()) for l in under(read_back_text, start) if l.strip()]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def flat(row):
    return " | ".join(f"{k}={' '.join(v.split())}" for k, v in row.items())


def short_hash(*parts):
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def row_prints(read_back_text, snapshot_raw):
    """A short fingerprint of what each grid row's answers were worked from, keyed "row 3" or
    "PO <number>". A row: its own line in Rows, and the price list snapshot. A PO: its own line in
    POs read, the house (the address Sam gave), and the snapshot. grid_carry.py uses these so a
    rebuilt grid keeps only the answers whose row did not change."""
    snap = hashlib.sha256(snapshot_raw or b"").hexdigest()
    the_house = " ".join(" ".join(under(read_back_text, "the house")).split())
    prints = {f"row {r.get('#', '').strip()}": short_hash(flat(r), snap)
              for r in prices.rows_table(read_back_text)}
    prints.update({f"PO {p.get('po number', '').strip()}": short_hash(flat(p), the_house, snap)
                   for p in as_dicts(under(read_back_text, "pos read"))})
    return prints


def house_facts(read_back_text, snapshot_raw):
    pos = as_dicts(under(read_back_text, "pos read"))
    return {"rows": prices.rows_table(read_back_text), "pos": pos,
            "po_numbers": [p.get("po number", "").strip() for p in pos],
            "extras": "\n".join(under(read_back_text, "extra items")),
            "prices": prices.parse(snapshot_raw)[0] if snapshot_raw else {}}


def expected_cells(read_back_text, snapshot_raw):
    """What code says for every cell: {"rows": [(key, {rule: cell})], "pos": [...]}."""
    house = house_facts(read_back_text, snapshot_raw)
    rows = [(r.get("#", "").strip(), {k: f(r, house) for k, f in rules.ROW_CHECKS.items()})
            for r in house["rows"]]
    pos = [(p.get("po number", "").strip(), {k: f(p, house) for k, f in rules.PO_CHECKS.items()})
           for p in house["pos"]]
    return {"rows": rows, "pos": pos}


def legend():
    lines = ["| Rule | Question | Filled by |", "|---|---|---|"]
    for group in (rules.ROW_RULES, rules.PO_RULES):
        lines += [f"| {k} | {q} | {who} |" for k, (q, who, _) in group.items()]
    return lines


def grid_table(first, keyed, ids):
    lines = ["| " + " | ".join([first] + list(ids)) + " |", "|" + "---|" * (len(ids) + 1)]
    return lines + ["| " + " | ".join([key] + [cells[i] for i in ids]) + " |" for key, cells in keyed]


def render(house, n, read_back_text, snapshot_raw):
    cells = expected_cells(read_back_text, snapshot_raw)
    head = ["---", f"house: {house}", f"attempt: {n}", "stage: 02 read",
            f"from: 02 read/{house}/read-back-{n}.md",
            f"read-back tables sha256: {tables_hash(read_back_text)}",
            "row sha256: " + "; ".join(f"{k} {v}" for k, v in row_prints(read_back_text, snapshot_raw).items()),
            "---", "",
            f"# {house}, rule grid {n}", "",
            "Built by `02 read/grid.py`. Code filled every cell it can work out. Answer each `?` one",
            "column at a time: take one rule, answer it for every row, then the next rule. Write the",
            "status, a colon, and what you looked at. Never change a cell code filled.", "",
            "## Rules", *legend(), "",
            "## Row grid", *grid_table("#", cells["rows"], rules.ROW_RULES), "",
            "## PO grid", *grid_table("PO number", cells["pos"], rules.PO_RULES), ""]
    return "\n".join(head)
