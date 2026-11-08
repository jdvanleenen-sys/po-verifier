"""Checking a rule grid against the read-back it was built from. See grid.py for how it is used."""
import re

import grid_rules as rules
from grid_read import expected_cells, table, tables_hash, under

HASH_LINE = re.compile(r"^read-back tables sha256:\s*([0-9a-f]{64})", re.M)
ROW_LIST = re.compile(r"\brows?\s+(\d+(?:\s*(?:,|and|&)\s*\d+)*)", re.I)
TRAP_WORDS = {"unit": "unit", "selection": "selection", "line-notes": "notes"}
SAM_ON_ROW = "(sam:"
GRIDS = (("row grid", "#", "rows", rules.ROW_RULES, "row"),
         ("po grid", "po number", "pos", rules.PO_RULES, "PO"))


def plain(text):
    return " ".join((text or "").split())


def split_status(cell):
    """('at risk', 'printed EA ...') for 'at risk: printed EA ...'; (None, '') if no known status."""
    for status in sorted(rules.STATUSES, key=len, reverse=True):
        if cell.lower().startswith(status.lower() + ":"):
            return status, cell[len(status) + 1:].strip()
    return None, ""


def answer_problem(cell, allowed):
    """What is wrong with the AI's answer to a '?' cell, or None."""
    if cell.strip() in ("", rules.ASK):
        return "not answered"
    status, said = split_status(cell)
    if status not in allowed:
        return f"'{cell}' must start with one of: " + ", ".join(f"'{s}:'" for s in allowed)
    return None if said else "say what you looked at after the colon"


def at_risk_rows(read_back_text, word):
    """Row numbers named in an 'At risk for this house' line that names this trap."""
    found = set()
    for line in under(read_back_text, "at risk"):
        if word not in line.lower():
            continue
        for group in ROW_LIST.findall(line):
            found.update(re.findall(r"\d+", group))
    return found


def check_cells(where, wanted, got, rule_specs, final, state):
    """Every cell of one grid row. state collects problems, ask-Sam count and at-risk rows."""
    for (rule, spec), code_said, cell in zip(rule_specs.items(), wanted, got):
        label = f"{where}, {rule}"
        if code_said != rules.ASK:
            if plain(cell) != plain(code_said):
                state["problems"].append(f"{label}: code says '{code_said}', the grid says '{cell}'")
            cell = code_said
        else:
            problem = answer_problem(cell, spec[2])
            if problem:
                state["problems"].append(f"{label}: {problem}")
                continue
        status, said = split_status(cell)
        if status == rules.FAIL:
            state["problems"].append(f"{label}: fail: {said}. Stop and ask Sam")
        elif status == rules.ASK_SAM:
            state["asks"] += 1
            if final:
                state["problems"].append(f"{label}: still waiting on Sam: {said}")
        elif status == rules.AT_RISK:
            state["risky"].add((where, rule))


def check_table(grid_text, expected, grid, final, state):
    heading, first, key, rule_specs, noun = grid
    header, rows = table(under(grid_text, heading))
    want_header = [first] + list(rule_specs)
    if header != want_header:
        state["problems"].append(f"{heading}: the columns are {header}, not {want_header}")
        return
    want_keys, got_keys = [k for k, _ in expected[key]], [r[0] for r in rows]
    if got_keys != want_keys:
        state["problems"].append(f"{heading}: has {noun}s {got_keys}; the read-back has {want_keys}")
        return
    for (k, cells), row in zip(expected[key], rows):
        if len(row) != len(header):
            state["problems"].append(f"{heading}, {noun} {k}: {len(row)} cells, not {len(header)}")
            continue
        where = f"row {k}" if noun == "row" else f"PO {k}"
        check_cells(where, [cells[r] for r in rule_specs], row[1:], rule_specs, final, state)


def check_grid(read_back_text, grid_text, snapshot_raw, final=False):
    """Every problem with the grid, and how many cells wait on Sam. No problems means it passes."""
    state = {"problems": [], "asks": 0, "risky": set()}
    recorded = HASH_LINE.search(grid_text or "")
    if not recorded:
        return ["the grid has no 'read-back tables sha256:' line; build it with grid.py"], 0
    if recorded.group(1) != tables_hash(read_back_text):
        state["problems"].append("the read-back's POs read, Rows or Extra items changed after the grid "
                                 "was built. Rebuild the grid and answer it again")
    expected = expected_cells(read_back_text, snapshot_raw)
    for grid in GRIDS:
        check_table(grid_text, expected, grid, final, state)
    for where, rule in sorted(state["risky"]):
        word = TRAP_WORDS.get(rule, rule)
        if where.split()[-1] not in at_risk_rows(read_back_text, word):
            state["problems"].append(f"{where} is at risk on {rule}, but no line under 'At risk for this "
                                     f"house' that says '{word}' names it")
    if final:
        state["problems"] += warning_problems(read_back_text)
    return state["problems"], state["asks"]


def warning_problems(read_back_text):
    """Each 'not on the price list' item Sam has not answered, or that the warning table leaves out.

    An unanswered item would reach compare unpriced without anyone deciding it should.
    """
    header, warned = table(under(read_back_text, "warning"))
    problems = [f"warning item {w[0]} '{w[1]}': no answer from Sam (add row / names item / leave unpriced)"
                for w in warned if len(w) < len(header) or not w[-1].strip()]
    rows_header, rows = table(under(read_back_text, "rows"))
    if "price list item" not in rows_header:
        return problems
    at = rows_header.index("price list item")
    unpriced = [r[0] for r in rows if len(r) > at and r[at].lower().startswith(rules.prices.UNPRICED)
                and SAM_ON_ROW not in r[at].lower()]
    if len(unpriced) > len(warned):
        problems.append(f"rows {', '.join(unpriced)} are not on the price list, but the warning table "
                        f"lists {len(warned)}. Every one goes in the warning table with Sam's answer")
    return problems


def not_comparable_rows(grid_text):
    """The read-back row numbers the grid marks 'not comparable' on the count rule."""
    header, rows = table(under(grid_text or "", "row grid"))
    if "count" not in header:
        return set()
    at = header.index("count")
    return {r[0] for r in rows if len(r) > at and split_status(r[at])[0] == rules.NOT_COMPARABLE}
