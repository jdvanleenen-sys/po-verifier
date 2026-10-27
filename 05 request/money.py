"""Work out what a house's request must say, from Sam's approved records only.

Reads the house's read-back (02 read), variance (03 compare) and review (04 review). Every number
the request may print is recomputed here from the read-back Sam said yes to and the decisions he
made in review. The AI's variance file is checked against that, never trusted. Anything that
cannot be read, or does not agree, is a problem, and a problem stops the request.
"""
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CENT = Decimal("0.01")
NO_PO = "none"
PO_NUMBER = re.compile(r"[A-Z]{2,}-\d+/\d+")
AMOUNT = re.compile(r"(\(?)([+\-−]?)\s*\$?\s*(\d[\d,]*(?:\.\d+)?)")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def read_text(path):
    """Read a record written by any editor: UTF-8 with or without a BOM, or UTF-16."""
    raw = Path(path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def to_amount(cell):
    """The first money amount in a cell, signed: '+$426.00', '-$170.00', '($170.00)', '$1,000.00'."""
    match = AMOUNT.search(cell or "")
    if not match:
        return None
    value = Decimal(match.group(3).replace(",", ""))
    negative = match.group(1) == "(" or match.group(2) in ("-", "−")
    return -value if negative else value


def to_number(cell):
    """The first plain number in a cell: '6 + 2 on EPO 01' gives 6."""
    match = NUMBER.search(cell or "")
    return Decimal(match.group(0).replace(",", "")) if match else None


def po_key(cell):
    """The PO number in a cell, or 'none' for an item on no PO."""
    match = PO_NUMBER.search(cell or "")
    return match.group(0) if match else NO_PO


def tables(text):
    """Every Markdown table in a text, keyed by the section heading above it."""
    found, heading, rows = {}, "", None
    for line in text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
        elif line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if rows is None:
                rows = {"header": [c.lower() for c in cells], "rows": []}
                found.setdefault(heading, rows)
            elif not all(set(c) <= set("-: ") for c in cells):
                rows["rows"].append(dict(zip(rows["header"], cells)))
        else:
            rows = None
    return found


def column(row, *starts):
    """The cell whose header starts with any of the given words."""
    for key, value in row.items():
        if any(key.startswith(s) for s in starts):
            return value
    return ""


def section(found, *words):
    for heading, table in found.items():
        if all(w in heading for w in words):
            return table["rows"]
    return []


def approved(text):
    """A record counts only with status: approved and a yes written in Sam's yes block."""
    status = re.search(r"^status:\s*(\S+)", text, re.M)
    answer = re.search(r"^-\s*Answer:\s*(.+)$", text, re.M)
    return bool(status and status.group(1).lower() == "approved"
                and answer and re.search(r"\byes\b", answer.group(1), re.I) is not None)


def read_back(text):
    """Sam's approved read-back: the rows, each PO's printed tax rate, and the EPOs."""
    found = tables(text)
    rows = [{
        "num": (column(r, "#") or "").strip(),
        "po": po_key(column(r, "po number")),
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
            rates[po_key(column(r, "po number"))] = tax / subtotal
    epos = [{
        "po": po_key(column(r, "po it is against")),
        "pays_for": column(r, "item it pays for").lower(),
        "total": to_amount(column(r, "total")) or Decimal(0),
        "sign": -1 if "back charge" in column(r, "which way").lower() else 1,
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
    """One variance row, recomputed from its read-back row. Returns the true variance."""
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
    return true_variance


def variance_rows(text, rb_rows, epos, problems):
    """Every variance row, each checked against Sam's read-back. Returns {(po, item): variance}."""
    result = {}
    for r in section(tables(text), "rows"):
        v = {"po": po_key(column(r, "po number")), "item": column(r, "item").strip().lower(),
             "rate": to_amount(column(r, "agreed rate")), "po_qty": to_number(column(r, "po qty")),
             "po_rate": to_amount(column(r, "po rate")), "po_amount": to_amount(column(r, "po amount")),
             "measured_qty": to_number(column(r, "measured qty")), "variance": to_amount(column(r, "variance"))}
        match = [rb for rb in rb_rows if rb["po"] == v["po"] and rb["item"] == v["item"]]
        if len(match) != 1:
            problems.append(f"variance row '{v['item']}' ({v['po']}) matches {len(match)} read-back rows, not 1. "
                            "Every item, including one on no PO, must be a row in the read-back's Rows table "
                            "(PO number 'none' for no PO), with Sam's yes on that read-back")
            continue
        result[(v["po"], v["item"])] = checked_row(v, match[0], epos, problems)
    for rb in rb_rows:
        if (rb["po"], rb["item"]) not in result:
            problems.append(f"read-back row {rb['num']} ('{rb['item']}') is missing from the variance")
    return result


def decisions(text, variances, problems):
    """Sam's on/off for each row he was shown. A row he did not choose is off."""
    chosen = {}
    for r in section(tables(text), ""):
        key = (po_key(column(r, "po number")), column(r, "item").strip().lower())
        decision = column(r, "sam's decision").strip().lower()
        if key not in variances:
            problems.append(f"review row '{key[1]}' ({key[0]}) is not in the variance")
        elif not (decision.startswith("on") or decision.startswith("off")):
            problems.append(f"review row '{key[1]}' has no on/off decision from Sam")
        elif to_amount(column(r, "variance")) != variances[key]:
            problems.append(f"review row '{key[1]}' shows {column(r, 'variance')}, the variance is {variances[key]}")
        else:
            chosen[key] = decision.startswith("on")
    return chosen


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
    """Everything the request must say, and every problem found on the way. records = 3 texts."""
    problems = []
    for name in ("read-back", "review"):
        if not approved(records[name]):
            problems.append(f"the {name} does not carry Sam's approval (status: approved and his yes)")
    rb_rows, rates, epos = read_back(records["read-back"])
    variances = variance_rows(records["variance"], rb_rows, epos, problems)
    chosen = decisions(records["review"], variances, problems)
    groups = {}
    for (po, item), on in chosen.items():
        if on:
            groups.setdefault(po, []).append((item, variances[(po, item)]))
    out = {"rows_on": [], "rows_off": [k[1] for k, on in chosen.items() if not on], "groups": {}}
    house = [Decimal(0), Decimal(0)]
    for po, rows in groups.items():
        before = sum((v for _, v in rows), Decimal(0))
        tax = (before * group_rate(po, rates, problems)).quantize(CENT, ROUND_HALF_UP)
        out["groups"][po] = {"before": before, "tax": tax, "total": before + tax}
        out["rows_on"] += [{"po": po, "item": i, "difference": v} for i, v in rows]
        house[0] += before
        house[1] += tax
    out["house"] = {"before": house[0], "tax": house[1], "total": house[0] + house[1]}
    out["po_numbers"] = sorted(set(rates))
    out["epo_names"] = [e["name"] for e in epos]
    return out, problems
