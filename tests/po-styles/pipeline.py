"""Run one PO style from styles.json through the code stages, the way a correct run would.

    records(style)        the read-back, rule grid, variance and review a correct run writes,
                          and the price list snapshot, as money.expected_request() takes them
    answer_key(style)     what the request must say, worked out here on its own (no stage code)
    request_text(...)     a request laid out the way reference/request-layout.html reads as text

The read-back is what an agent must write after reading the style's PO: the PO number as printed,
each line as printed, and plain numbers in the number columns. The grid is built by 02 read's own
code, with its open cells answered as Sam would. The variance is written by 03 compare's own code.
"""
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for stage in ("02 read", "03 compare", "05 request"):
    sys.path.insert(0, str(ROOT / stage))
import compare  # noqa: E402
import compare_rows  # noqa: E402
import grid_read  # noqa: E402
import prices  # noqa: E402
import seal  # noqa: E402

CENT = Decimal("0.01")
NO_PO = "none"


def money(v, signed=False):
    v = Decimal(v)
    sign = "+" if signed and v > 0 else "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}"


def rows_of(style):
    """Every read-back row, numbered in order: PO lines PO by PO, then the extra items."""
    rows = []
    for po in style["pos"]:
        rows += [dict(line, po=po["number"]) for line in po["lines"]]
    rows += [dict(e, po=NO_PO, ref="", desc="", unit="", qty=None, price=None) for e in style.get("extras", [])]
    for n, r in enumerate(rows, 1):
        r["num"] = str(n)
        r["total"] = Decimal(r["qty"]) * Decimal(r["price"]) if r["po"] != NO_PO else None
    return rows


def price_csv(style):
    lines = ["Item,Unit,Rate,Active"] + [f'"{item}",{unit},{rate},TRUE' for item, (unit, rate) in style["prices"].items()]
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")


def tax_lines(po, subtotal):
    """Each tax as the PO prints it: its own line, rounded on its own."""
    return [(label, Decimal(pct), (subtotal * Decimal(pct) / 100).quantize(CENT, ROUND_HALF_UP)) for label, pct in po["taxes"]]


def po_sums(po):
    subtotal = sum((Decimal(l["qty"]) * Decimal(l["price"]) for l in po["lines"]), Decimal(0))
    taxes = tax_lines(po, subtotal)
    return subtotal, taxes, subtotal + sum(t for _, _, t in taxes)


def pos_read(style):
    out = ["## POs read", "| PO number | Vendor | Job name and address | Lot/block/unit | Subtotal | Tax lines | Total |",
           "|---|---|---|---|---|---|---|"]
    for po in style["pos"]:
        subtotal, taxes, total = po_sums(po)
        shown = "; ".join(f"{label} {pct.normalize():f}% ${t:.2f}" for label, pct, t in taxes)
        if style.get("layout", {}).get("inclusive"):
            shown = "; ".join(f"{label} {pct.normalize():f}% included ${(subtotal * pct / (100 + pct)).quantize(CENT, ROUND_HALF_UP):.2f}"
                              for label, pct, _ in taxes)
            total = subtotal
        out.append(f"| {po['number']} | {style['painter']}, {style['vendor_no'] or 'no vendor number'} | {style['address']} | "
                   f"{style['lot'] or 'not printed'} | ${subtotal:.2f} | {shown} | ${total:.2f} |")
    return out


def epos_read(style):
    if not style.get("epos"):
        return ["## EPOs read", "none in the folder"]
    rows = {r["num"]: r for r in rows_of(style)}
    out = ["## EPOs read", "| EPO name | PO it is against | Item it pays for | Total | Which way the money goes | Notes |",
           "|---|---|---|---|---|---|"]
    out += [f"| {e['name']} | {e['against']} | row {e['row']}, {rows[str(e['row'])]['item']} | ${Decimal(e['total']):.2f} | "
            f"{e['way']} | {e['note']} |" for e in style["epos"]]
    return out


def measured_cell(r):
    if r.get("measured") is None:
        return f'"{r["words"]}"; nothing measured'
    sure = "; Sam confirmed" if r.get("confirmed") or r.get("cmp") is False else ""
    return f'"{r["words"]}"; {r["measured"]}{sure}'


def row_line(r, style):
    unit, rate = style["prices"].get(r["item"] or "", ("", ""))
    item = r["item"] or prices.UNPRICED
    on_po = r["po"] != NO_PO
    note = f"Markup {r['markup']} on unit cost ${r['printed_price']}" if r.get("markup") else "none printed"
    cells = [r["num"], r["po"], f"{r['ref']} {r['desc']}".strip() if on_po else "", r["unit"] if on_po else "",
             r["qty"] if on_po else "", f"${Decimal(r['price']):.2f}" if on_po else "",
             f"${r['total']:.2f}" if on_po else "", note if on_po else "", measured_cell(r), item, unit, rate]
    return "| " + " | ".join(cells) + " |"


def warning_lines(rows):
    """The warning table 02 read requires for every row not on the price list, with Sam's answer."""
    unpriced = [r for r in rows if not r["item"]]
    if not unpriced:
        return []
    return [f"## WARNING: not on the price list ({len(unpriced)} items)",
            "| PO number | Description as printed | Qty and unit | Closest items | Sam's answer |",
            "|---|---|---|---|---|",
            *[f"| {r['po']} | {r['desc'] or r['words']} | {r['qty']} {r['unit']} | none | leave unpriced |"
              for r in unpriced], ""]


def read_back(style, snapshot):
    rows = rows_of(style)
    risky = [r["num"] for r in rows if r["po"] != NO_PO and r["item"] and r["unit"] != style["prices"][r["item"]][0]]
    extras = [r for r in rows if r["po"] == NO_PO]
    return seal.seal_text("read-back-1.md", "\n".join([
        "---", f"house: {style['slug']}", "attempt: 1", "stage: 02 read", "status: draft",
        f"price list read: 2026-11-05, price-list-1.csv, sha256 {prices.fingerprint(snapshot)}", "---", "",
        f"# {style['slug']}, read-back 1", "", *warning_lines(rows), "## The house", f"{style['address']}; lot {style['lot']}; {style['builder']}.", "",
        "## At risk for this house",
        f"- Unit printed differs from the price list unit: rows {', '.join(risky)}." if risky else "- none", "",
        *pos_read(style), "", *epos_read(style), "",
        "## Rows", "| # | PO number | Line as printed | Unit as printed | PO qty | Unit price | Line total | Special option info | "
        "Sam measured (his words, size or count, colour, notes) | Price list item | Unit | Rate |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|", *[row_line(r, style) for r in rows], "",
        "## Extra items (in Sam's notes, on no PO)", *([f"- row {r['num']}: {r['words']}" for r in extras] or ["none"]), "",
        "## Sam's yes", "- Answer: yes, to the whole table", "- Name: Sam", "- Date: 2026-11-05", ""]))


ANSWERS = {"po-line-match": "pass: the PO line is this price list item", "note-match": "pass: Sam's note is this item",
           "line-notes": "pass: the note does not change what the line covers", "address": "pass: the address Sam gave"}


def grid(style, read_back_text, snapshot):
    """02 read's own grid, its open cells answered as Sam would answer them."""
    rows = {r["num"]: r for r in rows_of(style)}
    out, header = [], []
    for line in grid_read.render(style["slug"], 1, read_back_text, snapshot).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| ") and cells[0] in ("#", "PO number"):
            header = cells
        elif line.startswith("| ") and "?" in cells:
            row = rows.get(cells[0], {})
            for i, c in enumerate(cells):
                if c == "?" and header[i] == "count":
                    cells[i] = f"not comparable: {row['why']}" if row.get("cmp") is False else "pass: a count against the PO qty"
                elif c == "?":
                    cells[i] = ANSWERS[header[i]]
            line = "| " + " | ".join(cells) + " |"
        out.append(line)
    return "\n".join(out)


def variance(style, read_back_text, grid_text):
    compared, set_aside, problems = compare_rows.work_out(read_back_text, grid_text)
    limits = compare_rows.thresholds(compare_rows.CONTRACTOR.read_text(encoding="utf-8"))
    text = compare.render(style["slug"], 1, Path("read-back-1.md"), read_back_text, compared, set_aside, limits)
    return text, compared, problems


def review(style, compared):
    on = {str(n) for n in style["on"]}
    lines = ["---", f"house: {style['slug']}", "attempt: 1", "stage: 04 review", "status: draft", "---", "",
             "| Row | PO number | Item | Variance | Call | Sam's decision (on / off) | Reason, if a flagged row is taken off |",
             "|---|---|---|---|---|---|---|"]
    lines += [f"| {r['num']} | {r['po']} | {r['item']} | {money(r['variance'], True)} | shown | "
              f"{'on' if r['num'] in on else 'off (not chosen)'} | |" for r in compared]
    return seal.seal_text("review-1.md", "\n".join(lines + ["", "## Sam's yes", "- Answer: yes", "- Name: Sam",
                                                             "- Date: 2026-11-05", ""]))


def records(style):
    """(the records money.expected_request takes, problems the stages raised on the way)."""
    snapshot = price_csv(style)
    rb = read_back(style, snapshot)
    grid_text = grid(style, rb, snapshot)
    var_text, compared, problems = variance(style, rb, grid_text)
    return {"read-back": rb, "grid": grid_text, "variance": var_text, "review": review(style, compared),
            "price-list": snapshot}, problems


def answer_key(style):
    """{po: (before, tax, total)} for the rows Sam put on, worked out here: measured qty x agreed rate,
    less PO qty x PO price and any EPO already paid; each of the PO's taxes rounded on its own."""
    epo = {str(e["row"]): Decimal(e["total"]) for e in style.get("epos", [])}
    on = {str(n) for n in style["on"]}
    before = {}
    for r in rows_of(style):
        if r["num"] not in on:
            continue
        rate = Decimal(style["prices"][r["item"]][1])
        po_amount = (r["total"] or 0) + epo.get(r["num"], 0)
        before[r["po"]] = before.get(r["po"], Decimal(0)) + Decimal(r["measured"]) * rate - po_amount
    by_number = {po["number"]: po for po in style["pos"]}
    out = {}
    for po, b in before.items():
        taxes = tax_lines(by_number.get(po, style["pos"][0]), b)
        tax = sum((t for _, _, t in taxes), Decimal(0))
        out[po] = (b, tax, b + tax)
    return out


HEADINGS = "ITEM\nUNIT\nAGREED RATE\nPO QTY\nPO RATE\nPO AMOUNT\nMEASURED QTY\nMEASURED VALUE\nDIFFERENCE\nWHY\n"


def end_label(po, total):
    if po == NO_PO:
        return "New PO or EPO requested"
    return "Credit back to the builder for this PO" if total < 0 else "EPO requested for this PO"


def request_text(style, expected):
    """The request as its PDF reads as text: the three boxes, then one block per PO group."""
    house = expected["house"]
    by_number = {po["number"]: po for po in style["pos"]}
    total_label = "Total credit to the builder" if house["total"] < 0 else "Total requested"
    notes = "; ".join(f"{'No PO' if po == NO_PO else 'PO ' + po}: {money(g['total'])}" for po, g in expected["groups"].items())
    out = [f"Before tax\n{money(house['before'], True)}\n{len(expected['rows_on'])} items\nTax\n{money(house['tax'])}\n"
           f"{total_label}\n{money(house['total'])}\n{notes}\n"]
    for po, g in expected["groups"].items():
        rows = [r for r in expected["rows_on"] if r["po"] == po]
        taxes = by_number.get(po, style["pos"][0])["taxes"]
        heading = "No PO Work done on site that is on no PO." if po == NO_PO else f"PO {po} Interior paint."
        body = "".join("\n".join([r["label"], "EA", money(r["rate"]), f"{r['po_qty'].normalize():f}",
                                  money(r["rate"]) if po != NO_PO else "", money(r["po_amount"]),
                                  f"{r['measured_qty'].normalize():f}", money(r["measured_value"]),
                                  money(r["difference"], True), "Site count differs."]) + "\n" for r in rows)
        tax_label = " + ".join(f"{label} {Decimal(p).normalize():f}%" for label, p in taxes)
        out.append(f"{heading}\n{HEADINGS}{body}Difference before tax\n{money(g['before'], True)}\n"
                   f"{tax_label}, from this PO's own tax line\n{money(g['tax'])}\n{end_label(po, g['total'])}\n{money(g['total'])}\n")
    return "".join(out)
