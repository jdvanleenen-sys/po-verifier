"""The Difference screen: the variance's rows with what each needs from Sam, and his picks written
into review-N.md by code in the folder's own form, then sealed (seal.py runs the request's money
gate on a review before it seals it, so a review the request would refuse is never sealed).

Defaults follow 04 review: a flagged row is on, every other row is off, and three kinds of row have
no default (a flagged credit, a row whose difference is only an EPO already in its PO amount, and a
row on no PO when contractor.md says to ask which PO). Build the PDF waits until each is answered."""
import re
from decimal import Decimal

from folder import highest

DIFFERS = ("flag", "sam's call", "ignore")
NO_PO = "none"
OWN_GROUP = ""


def _money(cell):
    text = cell.replace("$", "").replace(",", "").replace("+", "").strip()
    return Decimal(text) if re.fullmatch(r"-?\d+(\.\d+)?", text) else None


def _variance(folder, house):
    path = highest(folder.stage("03 compare", house), "variance")
    if path is None:
        raise LookupError(f"{house} has no variance yet.")
    gr = folder.script("02 read", "grid_read")
    return path, gr.as_dicts(gr.under(path.read_text(encoding="utf-8"), "rows"))


def _no_po_rule(folder):
    contractor = folder.script("02 read", "contractor")
    text = (folder.root / "reference" / "contractor.md").read_text(encoding="utf-8-sig")
    rule = contractor.answer(text, "Work on no PO goes on").strip()
    return "" if rule.lower().startswith("ask each time") else rule


def _main_po(folder, house, rule):
    if "main po" not in rule.lower():
        return None
    read_back = highest(folder.stage("02 read", house), "read-back")
    return folder.script("05 request", "house_checks").main_po(read_back.read_text(encoding="utf-8"))


def _row(r, rule, main):
    variance = _money(r.get("variance", "")) or Decimal("0")
    call = r.get("call", "").strip().lower()
    credit = variance < 0
    epo_only = (r.get("measured qty", "").strip() == r.get("po qty", "").strip()
                and r.get("agreed rate", "").strip() == r.get("po rate", "").strip() and variance != 0)
    default = "on" if call == "flag" else "off"
    if (call == "flag" and credit) or epo_only:
        default = None
    no_po = r.get("po number", "").strip().lower() == NO_PO
    return {"row": r.get("row", "").strip(), "po": r.get("po number", "").strip(), "item": r.get("item", "").strip(),
            "variance": r.get("variance", "").strip(), "call": call, "why": r.get("why", "").strip(),
            "default": default, "credit": credit, "epo_only": epo_only, "no_po": no_po,
            "epo_goes_on": main if no_po else None, "epo_asks": no_po and main is None, "rule": rule if no_po else ""}


def screen(folder, house):
    """{"variance", "rows", "pos"}: rows that differ, in the variance's order, and the house's PO
    numbers (for a row on no PO when Sam is asked which PO it goes on)."""
    path, rows = _variance(folder, house)
    rule = _no_po_rule(folder)
    main = _main_po(folder, house, rule)
    differ = [_row(r, rule, main) for r in rows if r.get("call", "").strip().lower() in DIFFERS]
    pos = sorted({r.get("po number", "").strip() for r in rows} - {NO_PO, ""})
    return {"variance": f"03 compare/{house}/{path.name}", "rows": differ, "pos": pos}


def _decision(row, pick):
    """The decision, reason and EPO cells for one row from Sam's pick {"on", "reason", "epo"}."""
    if pick is None:
        if row["default"] is None:
            raise ValueError(f"Row {row['row']} ({row['item']}) needs your call: on or off.")
        on = row["default"] == "on"
        reason = ""
    else:
        on, reason = bool(pick.get("on")), " ".join(str(pick.get("reason", "")).split())
    if not on and row["call"] == "flag" and row["default"] == "on" and not reason:
        raise ValueError(f"Row {row['row']} ({row['item']}) is flagged. Say in a few words why it comes off.")
    word = "on" if on else ("off (Sam: " + reason + ")" if reason else "off (Sam did not choose it)")
    epo = ""
    if row["no_po"] and on:
        epo = row["epo_goes_on"] or ""
        if row["epo_asks"]:
            epo = (pick or {}).get("epo")
            if epo is None:
                raise ValueError(f"Row {row['row']} ({row['item']}) is on no PO. Pick the PO its EPO goes on, "
                                 "or its own No PO group.")
        reason = (reason + "; " if reason else "") + ("EPO goes on: standing answer, contractor.md"
                                                      if row["epo_goes_on"] else "")
    return word, reason, epo


def review_text(folder, house, picks):
    """The review file with Sam's picks, in the form of templates/review.md. His yes block is left
    empty: sam_yes writes it when he taps Build the PDF, then seals."""
    shown = screen(folder, house)
    unknown = set(picks) - {r["row"] for r in shown["rows"]}
    if unknown:
        raise ValueError("Those rows are out of date. Reload the screen.")
    attempt = _next_attempt(folder, house)
    lines = ["---", f"house: {house}", f"attempt: {attempt}", "stage: 04 review", "status: draft",
             f"from: {shown['variance']}", "---", "", f"# {house}, review {attempt}", "",
             "Written by the PO Checker app from Sam's picks on the Difference screen.", ""]
    if not any(_decision(r, picks.get(r["row"]))[0] == "on" for r in shown["rows"]):
        lines += ["Nothing to ask for: every row matches or Sam left it off.", ""]
    lines += ["| Row | PO number | Item | Variance | Call | Sam's decision (on / off) | "
              "Reason, if a flagged row is taken off | EPO goes on |", "|---|---|---|---|---|---|---|---|"]
    for r in shown["rows"]:
        word, reason, epo = _decision(r, picks.get(r["row"]))
        lines.append(f"| {r['row']} | {r['po']} | {r['item']} | {r['variance']} | {r['call']} | {word} | {reason} | {epo} |")
    lines += ["", "## Sam's yes", "- Answer:", "- Name:", "- Date:", ""]
    return "\n".join(lines)


def _next_attempt(folder, house):
    last = highest(folder.stage("04 review", house), "review")
    return int(last.stem.rsplit("-", 1)[1]) + 1 if last else 1
