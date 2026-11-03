"""The variance arithmetic: every comparable read-back row worked out by code. compare.py writes it.

Rows the grid marks "not comparable" and rows left off the price list are set apart, with no
dollars. Every other row gets its PO amount (with any EPO already issued for it), measured value,
variance, why and call.

This arithmetic is written apart from the money gate (05 request/money.py) on purpose. The gate
checks this file; if both shared one calculation, a mistake in it would pass both.
"""
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "02 read"))
import grid_check  # noqa: E402
import grid_rules as rules  # noqa: E402
import prices  # noqa: E402
from grid_read import as_dicts, table, under  # noqa: E402

CONTRACTOR = ROOT / "reference" / "contractor.md"
OTHER_TRADE = ("another trade", "other trade")


def thresholds(text):
    """(ignore line, flag line, source note) from reference/contractor.md, the only home for them."""
    ignore = re.search(r"Ignore line\s*\|\s*under \$([\d,]+)", text)
    flag = re.search(r"Flag line\s*\|\s*\$([\d,]+) and up", text)
    if not ignore or not flag:
        sys.exit("reference/contractor.md does not give the ignore line and flag line. Run 00 setup.")
    approved = re.search(r"^status:\s*approved", text, re.M)
    stand_in = "practice stand-in" in text.lower()
    if not approved and not stand_in:
        sys.exit("reference/contractor.md is not approved. Ask Sam to approve it in 00 setup.")
    note = "approved" + (", practice stand-ins" if stand_in else "")
    return Decimal(ignore.group(1).replace(",", "")), Decimal(flag.group(1).replace(",", "")), note


def sams_yes(text):
    status = re.search(r"^status:\s*(\S+)", text, re.M)
    answer = re.search(r"^-\s*Answer:\s*(.+)$", text, re.M)
    return bool(status and status.group(1).lower() == "approved"
                and answer and re.search(r"\byes\b", answer.group(1), re.I))


def money(value, signed=False):
    sign = "+" if signed and value > 0 else "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def epo_sign(which_way):
    """A back charge against Sam takes money away. One against another trade still pays Sam."""
    text = which_way.lower()
    return -1 if "back charge" in text and not any(o in text for o in OTHER_TRADE) else 1


def epos_by_row(read_back_text, problems):
    """{row number: (signed EPO money, [EPO names])} from the EPOs read table."""
    found = {}
    for e in as_dicts(under(read_back_text, "epos read")):
        named = re.search(r"\brow (\d+)\b", e.get("item it pays for", ""), re.I)
        total = rules.number(e.get("total", ""))
        if not named or total is None:
            problems.append(f"EPO {e.get('epo name', '?')}: no 'row N' in 'Item it pays for', or no total")
            continue
        amount, names = found.get(named.group(1), (Decimal(0), []))
        signed = total * epo_sign(e.get("which way the money goes", ""))
        found[named.group(1)] = (amount + signed, names + [(e.get("po it is against", "").strip(), signed)])
    return found


def why(row):
    if row["po"] == rules.NO_PO:
        return "missing from every PO"
    reasons = []
    if row["measured_qty"] > row["po_qty"]:
        reasons.append("PO quantity short")
    elif row["measured_qty"] < row["po_qty"]:
        reasons.append("PO quantity over")
    if row["po_rate"] != row["rate"]:
        reasons.append("PO rate differs from the agreed rate")
    if row["epo"]:
        reasons.append(f"EPO {money(row['epo'], True)} counted in the PO amount")
    return "; ".join(reasons) or "matches"


def call(variance, ignore, flag):
    size = abs(variance)
    if size == 0:
        return "matches"
    if size < ignore:
        return "ignore"
    return "flag" if size >= flag else "Sam's call"


def priced_row(r, epos, problems):
    """One comparable read-back row, worked out. Every number comes from the read-back."""
    num, po = r.get("#", "").strip(), rules.po_of(r)
    epo, against = epos.get(num, (Decimal(0), []))
    if any(p != po for p, _ in against):
        problems.append(f"row {num}: an EPO for it is against a different PO than {po}")
    on_po = po != rules.NO_PO
    row = {"num": num, "po": po, "item": r.get("price list item", "").strip(), "unit": r.get("unit", "").strip(),
           "rate": rules.number(r.get("rate", "")), "measured_qty": rules.measured_qty(r), "epo": epo,
           "po_qty": rules.number(rules.cell(r, "po qty")) if on_po else Decimal(0),
           "po_rate": rules.number(rules.cell(r, "unit price")) if on_po else None}
    if None in (row["rate"], row["measured_qty"], row["po_qty"]) or (on_po and row["po_rate"] is None):
        problems.append(f"row {num}: a rate or quantity is not a number in the read-back")
        return None
    row["po_amount"] = row["po_qty"] * (row["po_rate"] or 0) + epo
    row["measured_value"] = row["measured_qty"] * row["rate"]
    row["variance"] = row["measured_value"] - row["po_amount"]
    return row


def work_out(read_back_text, grid_text):
    """(compared rows, set-aside rows, problems) for an approved read-back and its grid."""
    problems = []
    epos = epos_by_row(read_back_text, problems)
    not_comparable = grid_check.not_comparable_rows(grid_text)
    count_cells = dict(grid_check_counts(grid_text))
    compared, set_aside = [], []
    for r in prices.rows_table(read_back_text):
        num = r.get("#", "").strip()
        if rules.item_state(r) != "priced":
            set_aside.append((r, r.get("price list item", "").strip()))
        elif num in not_comparable:
            set_aside.append((r, count_cells.get(num, "not comparable")))
        else:
            row = priced_row(r, epos, problems)
            if row:
                compared.append(row)
    return compared, set_aside, problems


def grid_check_counts(grid_text):
    """(row number, count cell) for every row of the grid."""
    header, rows = table(under(grid_text, "row grid"))
    if "count" not in header:
        return []
    at = header.index("count")
    return [(r[0], r[at]) for r in rows if len(r) > at]
