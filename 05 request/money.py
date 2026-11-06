"""Work out what a house's request must say, from Sam's approved records only.

Reads the house's read-back (02 read), variance (03 compare) and review (04 review). Every number
the request may print is recomputed here from the read-back Sam said yes to and the decisions he
made in review. The AI's variance file is checked against that, never trusted. Anything that
cannot be read, or does not agree, is a problem, and a problem stops the request.
"""
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02 read"))
import prices  # noqa: E402
from records import (  # noqa: E402,F401  (callers use money.column, money.read_text, ...)
    NUMBER, AMOUNT, approved, column, read_text, section, tables, to_amount, to_number)
import grid_check  # noqa: E402

CENT = Decimal("0.01")
NO_PO = "none"
PO_NUMBER = re.compile(r"[A-Z]{2,}-\d+/\d+")


def po_key(cell, known=None):
    """The PO number in a cell, or 'none' for an item on no PO.

    known: the PO numbers the read-back lists under "POs read". Builders shape PO numbers in their
    own way (MKR-02402401/027, SRH-2026-0417, 4500012345), so a cell is matched against those, the
    longest first. A cell naming none of them is returned as written, and fails where it is used."""
    text = (cell or "").strip()
    if text.lower() in ("", NO_PO):
        return NO_PO
    if known:
        return max((k for k in known if k.lower() in text.lower()), key=len, default=text)
    match = PO_NUMBER.search(text)
    return match.group(0) if match else text


def takes_from_sam(which_way):
    """-1 for a back charge against Sam. A back charge against another trade still pays Sam: +1."""
    text = which_way.lower()
    return -1 if "back charge" in text and "other trade" not in text else 1


def pos_listed(found):
    """The PO numbers as the read-back's "POs read" table writes them."""
    return {c for r in section(found, "pos read") if (c := column(r, "po number").strip()) and c.lower() != NO_PO}


def read_back(text):
    """Sam's approved read-back: the rows, each PO's printed tax rate, and the EPOs."""
    found = tables(text)
    known = pos_listed(found)
    rows = [{
        "num": (column(r, "#") or "").strip(),
        "po": po_key(column(r, "po number"), known),
        "line": column(r, "line as printed").strip(),
        "item": column(r, "price list item").strip().lower(),
        "po_qty": to_number(column(r, "po qty")),
        "unit_price": to_amount(column(r, "unit price")),
        "rate": to_amount(column(r, "rate")),
        "measured": column(r, "sam measured"),
    } for r in section(found, "rows")]
    rates = {}
    for r in section(found, "pos read"):
        subtotal = to_amount(column(r, "subtotal"))
        tax = sum((to_amount(m.group(0)) for m in re.finditer(r"\$[\d,]+\.\d\d", column(r, "tax lines"))),
                  Decimal(0))
        if subtotal:
            rates[po_key(column(r, "po number"), known)] = tax / subtotal
    epos = [{
        "po": po_key(column(r, "po it is against"), known),
        "pays_for": column(r, "item it pays for").lower(),
        "total": to_amount(column(r, "total")) or Decimal(0),
        "sign": takes_from_sam(column(r, "which way")),
        "name": column(r, "epo name"),
    } for r in section(found, "epos read") if to_amount(column(r, "total")) is not None]
    return rows, rates, epos


def epo_amount(rb_row, epos):
    """EPOs already issued for this row count in its PO amount (a back charge counts against)."""
    total = Decimal(0)
    for e in epos:
        names_row = f"row {rb_row['num']}" in e["pays_for"] or rb_row["item"] in e["pays_for"]
        if e["po"] == rb_row["po"] and names_row:
            total += e["total"] * e["sign"]
    return total


def checked_row(v, rb, epos, problems):
    """One variance row, recomputed from its read-back row. Returns the row's true figures:
    {"rate", "po_qty", "po_amount", "measured_qty", "measured_value", "difference"}. PO qty is the
    PO's own count (0 on no PO); the PO amount includes any EPO already issued for the row."""
    where = f"variance row '{v['item']}' ({v['po']})"
    if v["rate"] != rb["rate"]:
        problems.append(f"{where}: agreed rate {v['rate']}, read-back says {rb['rate']}")
    po_amount = Decimal(0)
    if rb["po"] != NO_PO:
        if v["po_qty"] != rb["po_qty"] or v["po_rate"] != rb["unit_price"]:
            problems.append(f"{where}: PO qty or rate differs from the read-back")
        po_amount = (rb["po_qty"] or 0) * (rb["unit_price"] or 0) + epo_amount(rb, epos)
    measured_numbers = {to_number(n) for n in NUMBER.findall(rb["measured"])}
    if v["measured_qty"] not in measured_numbers:
        problems.append(f"{where}: measured qty {v['measured_qty']} is not in Sam's notes as read back")
    true_variance = (v["measured_qty"] or 0) * (rb["rate"] or 0) - po_amount
    if v["po_amount"] != po_amount or v["variance"] != true_variance:
        problems.append(f"{where}: says PO amount {v['po_amount']} and variance {v['variance']}; "
                        f"the read-back gives {po_amount} and {true_variance}")
    rate = rb["rate"] or Decimal(0)
    return {"rate": rate, "po_qty": rb["po_qty"] or Decimal(0), "po_amount": po_amount,
            "measured_qty": v["measured_qty"] or Decimal(0), "measured_value": (v["measured_qty"] or 0) * rate,
            "difference": true_variance}


def variance_rows(text, rb_rows, epos, problems, set_aside=frozenset()):
    """Every variance row, each checked against Sam's read-back. Returns {(po, item, read-back row
    number): figures}, the figures as checked_row() gives them. A variance with a Row column is
    matched row by row; one without it (written before 2026-11-05) by PO and item, which must then
    name one read-back row.

    set_aside: read-back row numbers the rule grid marks not comparable. They get no dollars.
    """
    result, known = {}, {rb["po"] for rb in rb_rows}
    for r in section(tables(text), "rows"):
        row_num = column(r, "row").strip() or None
        v = {"po": po_key(column(r, "po number"), known), "item": column(r, "item").strip().lower(),
             "rate": to_amount(column(r, "agreed rate")), "po_qty": to_number(column(r, "po qty")),
             "po_rate": to_amount(column(r, "po rate")), "po_amount": to_amount(column(r, "po amount")),
             "measured_qty": to_number(column(r, "measured qty")), "variance": to_amount(column(r, "variance"))}
        if v["item"].startswith(prices.UNPRICED):
            problems.append(f"variance row '{v['item']}' ({v['po']}) is unpriced, so it belongs in the "
                            "'Not comparable, or left unpriced' list with no dollars, not in the Rows table")
            continue
        match = [rb for rb in rb_rows if rb["po"] == v["po"] and rb["item"] == v["item"]
                 and row_num in (None, rb["num"])]
        if len(match) == 1 and match[0]["num"] in set_aside:
            problems.append(f"variance row '{v['item']}' ({v['po']}) is marked not comparable in the rule grid, "
                            "so it belongs in the 'Not comparable' list with no dollars")
            continue
        if len(match) != 1:
            problems.append(f"variance row '{v['item']}' ({v['po']}) matches {len(match)} read-back rows, not 1. "
                            "Every item, including one on no PO, must be a row in the read-back's Rows table "
                            "(PO number 'none' for no PO), with Sam's yes on that read-back")
            continue
        key = (v["po"], v["item"], match[0]["num"])
        if key in result:
            problems.append(f"read-back row {key[2]} ('{v['item']}') is in the variance twice")
        result[key] = checked_row(v, match[0], epos, problems)
    for rb in rb_rows:
        if all(k[2] != rb["num"] for k in result) and not unpriced(rb) and rb["num"] not in set_aside:
            problems.append(f"read-back row {rb['num']} ('{rb['item']}') is missing from the variance")
    return result


def unpriced(rb_row):
    """A row Sam left unpriced: no rate, no measured value, no call, never on a request."""
    return rb_row["item"].startswith(prices.UNPRICED)


def decisions(text, variances, problems):
    """Sam's on/off for each row he was shown. A row he did not choose is off."""
    chosen, known = {}, {k[0] for k in variances}
    for r in section(tables(text), ""):
        po, item = po_key(column(r, "po number"), known), column(r, "item").strip().lower()
        row_num = column(r, "row").strip() or None
        keys = [k for k in variances if k[:2] == (po, item) and row_num in (None, k[2])]
        key = keys[0] if len(keys) == 1 else (po, item, row_num)
        decision = column(r, "sam's decision").strip().lower()
        if len(keys) > 1:
            problems.append(f"review row '{item}' ({po}) could be any of read-back rows "
                            f"{', '.join(k[2] for k in keys)}; give each its Row number")
        elif key in chosen:
            problems.append(f"review row '{item}' ({po}, row {key[2]}) is in the review twice")
        elif not keys:
            problems.append(f"review row '{item}' ({po}) is not in the variance")
        elif not (decision.startswith("on") or decision.startswith("off")):
            problems.append(f"review row '{key[1]}' has no on/off decision from Sam")
        elif to_amount(column(r, "variance")) != variances[key]["difference"]:
            problems.append(f"review row '{key[1]}' shows {column(r, 'variance')}, "
                            f"the variance is {variances[key]['difference']}")
        else:
            chosen[key] = decision.startswith("on")
    return chosen


LINE_REF = re.compile(r"^\(?(\d+(?:\.\d+)*)\)?\s")


def row_label(item, num, rows, lines):
    """The name a row prints under on the request: its price list item, and when that item is on
    more than one approved row of the same PO, the PO's own line number too ("walls, PO line 3.01"),
    or the line as printed when the PO numbers no lines."""
    if sum(1 for i, _, _ in rows if i == item) == 1:
        return item
    ref = LINE_REF.match(lines.get(num, "") + " ")
    return f"{item}, PO line {ref.group(1)}" if ref else f"{item}, {lines.get(num) or 'row ' + num}"


def group_rate(po, rates, problems):
    """Tax for a PO group comes from that PO's own printed figures; 'no PO' needs one house rate."""
    if po != NO_PO:
        if po not in rates:
            problems.append(f"no printed tax found for {po} in the read-back")
        return rates.get(po, Decimal(0))
    distinct = set(rates.values())
    if len(distinct) != 1:
        problems.append("the POs carry different tax rates, so the 'no PO' group needs Sam to say which")
        return Decimal(0)
    return distinct.pop()


def expected_request(records):
    """Everything the request must say, and every problem found on the way.

    records: the read-back, variance and review texts, "grid", the rule grid built for that
    read-back (None if there is none), and "price-list", the bytes of the price list snapshot the
    read-back names (None if it is missing).
    """
    problems = []
    for name in ("read-back", "review"):
        if not approved(records[name]):
            problems.append(f"the {name} does not carry Sam's approval (status: approved and his yes)")
    problems += prices.check_read_back(records["read-back"], records.get("price-list"))
    grid_text = records.get("grid")
    if grid_text is None:
        problems.append("the read-back has no rule grid (run: python \"02 read/grid.py\" build <house>)")
    else:
        problems += grid_check.check_grid(records["read-back"], grid_text, records.get("price-list"), final=True)[0]
    rb_rows, rates, epos = read_back(records["read-back"])
    set_aside = grid_check.not_comparable_rows(grid_text)
    variances = variance_rows(records["variance"], rb_rows, epos, problems, set_aside)
    chosen = decisions(records["review"], variances, problems)
    groups, lines = {}, {rb["num"]: rb["line"] for rb in rb_rows}
    for (po, item, num), on in chosen.items():
        if on:
            groups.setdefault(po, []).append((item, num, variances[(po, item, num)]))
    out = {"rows_on": [], "rows_off": [k[1] for k, on in chosen.items() if not on], "groups": {}}
    house = [Decimal(0), Decimal(0)]
    for po, rows in groups.items():
        before = sum((v["difference"] for _, _, v in rows), Decimal(0))
        rate = group_rate(po, rates, problems)
        tax = (before * rate).quantize(CENT, ROUND_HALF_UP)
        out["groups"][po] = {"before": before, "tax": tax, "total": before + tax}
        out.setdefault("rates", {})[po] = rate
        out["rows_on"] += [{"po": po, "item": i, "row": n, "label": row_label(i, n, rows, lines), **v}
                           for i, n, v in rows]
        house[0] += before
        house[1] += tax
    out["house"] = {"before": house[0], "tax": house[1], "total": house[0] + house[1]}
    out["po_numbers"] = sorted(set(rates))
    out["epo_names"] = [e["name"] for e in epos]
    # Amounts a row's why or a PO rate may print besides the row and group figures.
    out["other_amounts"] = sorted({r["unit_price"] for r in rb_rows if r.get("unit_price") is not None} |
                                  {e["total"] for e in epos})
    return out, problems
