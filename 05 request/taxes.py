"""The tax rate each PO charges, and the PO each chosen row's EPO goes on. Split out of money.py."""
import re
from decimal import Decimal, ROUND_HALF_UP

from records import column, section, tables, to_amount

CENT = Decimal("0.01")
NO_PO = "none"


TAX_PART = re.compile(r"(\d+(?:\.\d+)?)\s?%")
TAX_AMOUNT = re.compile(r"\$[\d,]+\.\d\d")


def printed_rates(subtotal, tax_cell):
    """Each tax the PO charges, as a fraction: (0.05,) for GST, (0.05, 0.09975) for GST and QST.

    Where every tax line prints its percentage and that percentage of the subtotal is the amount it
    prints, the percentages are used, and each tax is worked out and rounded on its own, as the PO
    does. Otherwise the one rate the printed figures give: all the tax over the subtotal."""
    parts = [(TAX_PART.search(p), to_amount(a.group(0))) for p in tax_cell.split(";") if (a := TAX_AMOUNT.search(p))]
    charged = [(pct, amount) for pct, amount in parts if amount]
    if charged and all(pct for pct, _ in charged):
        fractions = tuple(Decimal(pct.group(1)) / 100 for pct, _ in charged)
        if all((subtotal * f).quantize(CENT, ROUND_HALF_UP) == amount for f, (_, amount) in zip(fractions, charged)):
            return fractions
    return (sum((amount for _, amount in parts), Decimal(0)) / subtotal,)


def epo_targets(text, chosen, house_pos, problems):
    """The PO whose EPO each chosen row goes on, from the review's 'EPO goes on' column.

    Blank means the row's own PO (a row on no PO stays in the "No PO" group). Only a row on no PO
    may be named onto a PO, and only a PO in this house.
    """
    targets = {}
    for r in section(tables(text), ""):
        named = column(r, "epo goes on").strip()
        num, item = column(r, "row").strip() or None, column(r, "item").strip().lower()
        keys = [k for k in chosen if k[1] == item and num in (None, k[2])]
        if not named or len(keys) != 1:
            continue
        key, target = keys[0], next((p for p in house_pos if p.lower() == named.lower()), named)
        if target not in house_pos:
            problems.append(f"review row '{item}' names {named} under 'EPO goes on', which is not a PO in this house")
        elif key[0] != NO_PO and target != key[0]:
            problems.append(f"review row '{item}' is on PO {key[0]}; only work on no PO can go on another PO's EPO")
        else:
            targets[key] = target
    return targets


def group_rate(po, rates, problems):
    """The taxes for a PO group, from that PO's own printed figures; 'no PO' needs one house rate."""
    if po != NO_PO:
        if po not in rates:
            problems.append(f"no printed tax found for {po} in the read-back")
        return rates.get(po, (Decimal(0),))
    distinct = set(rates.values())
    if len(distinct) != 1:
        problems.append("the POs carry different tax rates, so the 'no PO' group needs Sam to say which")
        return (Decimal(0),)
    return distinct.pop()
