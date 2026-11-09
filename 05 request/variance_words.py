"""The words compare writes beside the money: each row's Why and Call, and the house-flag line.

The money gate checks every dollar in the variance; these words decide what Sam is shown and what
goes on by default, so they are worked out again here from the figures the gate already checked.
Written apart from 03 compare on purpose: if both shared one rule, a mistake in it would pass both.
"""
import re
from decimal import Decimal

from records import column, section, tables, to_amount

NO_PO = "none"
IGNORE = re.compile(r"Ignore line\s*\|\s*under \$([\d,]+)")
FLAG = re.compile(r"Flag line\s*\|\s*\$([\d,]+) and up")
HOUSE_FLAG = re.compile(r"House flagged on total:\s*(yes|no)\b", re.I)
REDO = "The variance was changed by hand: delete it and run compare.py again"
TOTALS = (("Total of POs", "po_amount"), ("Total measured value", "measured_value"), ("Total variance", "difference"))


def total_problems(variance_text, figures):
    """The totals lines are the sums of the compared rows' checked figures (loop run 6: a hand-edited
    'Total variance' passed while every row was right)."""
    out = []
    for label, key in TOTALS:
        m = re.search(rf"^-\s*{label}:\s*(.+)$", variance_text or "", re.M)
        if not m or not figures or any(key not in f for f in figures.values()):
            continue
        want = sum((f[key] for f in figures.values()), Decimal(0))
        said = to_amount(m.group(1))
        if said != want:
            out.append(f"the variance's '{label}' line says {money(said) if said is not None else 'nothing'}; "
                       f"its rows add up to {money(want)}. {REDO}")
    return out


def limits(setup_text):
    """(ignore line, flag line) from contractor.md, or None when it gives neither."""
    i, f = IGNORE.search(setup_text or ""), FLAG.search(setup_text or "")
    if not i or not f:
        return None
    return Decimal(i.group(1).replace(",", "")), Decimal(f.group(1).replace(",", ""))


def money(value):
    sign = "+" if value > 0 else "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def call(variance, ignore, flag):
    size = abs(variance)
    if size == 0:
        return "matches"
    if size < ignore:
        return "ignore"
    return "flag" if size >= flag else "sam's call"


def why(po, f):
    """The reasons for one row, from its checked figures."""
    if po == NO_PO:
        return "missing from every po"
    reasons = []
    if f["measured_qty"] > f["po_qty"]:
        reasons.append("po quantity short")
    elif f["measured_qty"] < f["po_qty"]:
        reasons.append("po quantity over")
    if f.get("po_rate") is not None and f["po_rate"] != f["rate"]:
        reasons.append("po rate differs from the agreed rate")
    epo = f["po_amount"] - f["po_qty"] * (f.get("po_rate") or 0)
    if epo:
        reasons.append(f"epo {money(epo)} counted in the po amount")
    return "; ".join(reasons) or "matches"


def problems(variance_text, figures, setup_text):
    """Every Why, Call or house-flag line in the variance that its own figures do not give."""
    totals = total_problems(variance_text, figures)
    found = limits(setup_text)
    if found is None:
        return totals
    ignore, flag = found
    out = []
    for r in section(tables(variance_text), "rows"):
        num, po_cell = column(r, "row").strip(), column(r, "po number").strip().lower()
        item = column(r, "item").strip().lower()
        keys = [k for k in figures if (k[2] == num if num else (k[0].lower() == po_cell and k[1] == item))]
        if len(keys) != 1:
            continue
        po, f = keys[0][0], figures[keys[0]]
        want_why, want_call = why(po, f), call(f["difference"], ignore, flag)
        said_why, said_call = column(r, "why").strip().lower(), column(r, "call").strip().lower()
        if said_why != want_why or said_call != want_call:
            out.append(f"variance row {num or item} says Why '{said_why}' and Call '{said_call}'; its figures give "
                       f"'{want_why}' and '{want_call}'. {REDO}")
    total = sum((f["difference"] for f in figures.values()), Decimal(0))
    said = HOUSE_FLAG.search(variance_text or "")
    want = "yes" if abs(total) >= flag else "no"
    if said and said.group(1).lower() != want:
        out.append(f"the variance says the house is{'' if said.group(1).lower() == 'yes' else ' not'} flagged; "
                   f"its total {money(total)} against the flag line ${flag:,.2f} says {want}. {REDO}")
    return totals + out
