"""Carrying answers into a rebuilt grid, so `grid.py build <house> --replace` never loses one.

Each grid records a short fingerprint of every row and PO it was built from (grid_read.row_prints).
When a draft read-back's grid is rebuilt, an answered cell is carried into the new grid only when
its row's fingerprint is the same in both grids, the rule is still one the AI answers, and code did
not fill that cell this time. Every other answered cell is listed, with what it said, so it is
asked again: an answer is never kept for a row that changed, and never dropped without a word.
"""
import re

import grid_rules as rules
from grid_read import table, under

PRINTS = re.compile(r"^row sha256:[ \t]*(.*)$", re.M)
GRIDS = (("row grid", "row", rules.ROW_RULES), ("po grid", "PO", rules.PO_RULES))


def prints_of(grid_text):
    """{"row 3": fingerprint, "PO <number>": fingerprint} from a grid; {} for a grid built before
    grids recorded them."""
    found = PRINTS.search(grid_text or "")
    if not found:
        return {}
    pairs = [part.strip().rsplit(" ", 1) for part in found.group(1).split(";") if part.strip()]
    return {p[0]: p[1] for p in pairs if len(p) == 2}


def ai_cells(grid_text):
    """{("row 3", rule): cell} for every cell of a rule the AI answers, filled or '?'."""
    found = {}
    for heading, noun, specs in GRIDS:
        header, rows = table(under(grid_text, heading))
        for row in rows:
            found.update({(f"{noun} {row[0]}", rule): cell.strip() for rule, cell in zip(header[1:], row[1:])
                          if specs.get(rule, (None, None, ()))[2]})
    return found


def answered(grid_text):
    return {k: c for k, c in ai_cells(grid_text).items() if c not in ("", rules.ASK)}


def carry(old_grid, new_grid):
    """(new grid text with the carried answers in, how many were carried, [each answer not carried])."""
    old, before, now = answered(old_grid), prints_of(old_grid), prints_of(new_grid)
    lines, header, noun, carried = [], [], None, set()
    for line in new_grid.splitlines():
        if line.startswith("#"):
            noun, header = next((n for h, n, _ in GRIDS if line.lstrip("#").strip().lower() == h), None), []
        elif noun and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not header:
                header = cells
            elif rules.ASK in cells and len(cells) == len(header):
                where = f"{noun} {cells[0]}"
                same = where in before and before.get(where) == now.get(where)
                for i, cell in enumerate(cells):
                    if cell == rules.ASK and same and (where, header[i]) in old:
                        cells[i] = old[(where, header[i])]
                        carried.add((where, header[i]))
                line = "| " + " | ".join(cells) + " |"
        lines.append(line)
    rebuilt = "\n".join(lines) + ("\n" if new_grid.endswith("\n") else "")
    new_cells = ai_cells(rebuilt)  # a cell code fills now needs no answer; a missing one is gone
    lost = [f"{where}, {rule}: was '{cell}'" for (where, rule), cell in old.items()
            if (where, rule) not in carried and new_cells.get((where, rule), rules.ASK) == rules.ASK]
    return rebuilt, len(carried), lost


def message(name, asks, carried, lost):
    """What grid.py build --replace prints."""
    text = (f"{name} written: {carried} answer(s) carried from the grid it replaces; "
            f"{asks} cell(s) are '?' for you to answer, one rule at a time.")
    if lost:
        text += ("\nThese answers were not carried, because their row changed or is gone (or the old grid "
                 "was built before grids recorded rows). Ask each one again:\n- " + "\n- ".join(lost))
    return text
