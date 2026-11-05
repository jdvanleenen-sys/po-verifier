"""Write each test house's intake files and Sam's answers from houses.json. Run from the repo root:

    python tests/houses/make_houses.py

For each house it writes tests/houses/<slug>/intake/ (the POs and EPOs laid out like the practice
POs in 01 intake/77-mockup-drive, the site notes, house-info.md) and tests/houses/<slug>/sam-answers.md.
It refuses a PO whose 5% GST is not a whole number of cents, so every printed figure is exact.
"""
import html
import json
import sys
from decimal import Decimal
from pathlib import Path

import handwriting

HERE = Path(__file__).resolve().parent
GST = Decimal("0.05")
CENT = Decimal("0.01")
DEFAULT_PRICE_DATE = "07/15/2026"
BUILDER = "Sample Builder Ltd."
VENDOR = ("Sample Painting Co.", "V00999")
FONT = '<font face="arial" style="font-size:12px;">'
CELL = 'style="border-top:1px solid black;padding-top:15px;'
SEL_ONE = "1.000000000000000e+000"


def money(value):
    return f"${value:.2f}"


def pair(label, value):
    return (f'<tr><td width="115" valign="top">{FONT}<b>{label}:</b></font></td>'
            f'<td width="210" valign="top">{FONT}{value}&nbsp;</font></td></tr>')


def line_rows(line, option_name):
    """One PO line and its special option block, as the practice POs print them."""
    desc, uom, qty, price = line[:4]
    notes = line[4] if len(line) > 4 else ""
    total = Decimal(qty) * Decimal(price)
    selection = qty if "Finished Areas" in desc else SEL_ONE
    cells = [("(5120)", f'{CELL}padding-left:5px"'), (html.escape(desc) + "  :", f'{CELL}"'),
             (uom, f'align="right" {CELL}"'), (qty, f'align="right" {CELL}padding-left:20px;"'),
             (f"&nbsp;${Decimal(price):.2f}&nbsp;", f'align="right" {CELL}"'),
             (f"&nbsp;{money(total)}&nbsp;", f'align="right" {CELL}"')]
    row = "<tr>\n" + "\n".join(f"<td {attrs}>{FONT}{text}</font></td>" for text, attrs in cells) + "\n</tr>\n"
    extra = f"Notes: {html.escape(notes)}<br>" if notes else ""
    info = (f'<tr><td></td><td style="padding-top:10px;">{FONT}<b>Special Option Information:</b><br>\n'
            f"Option Name: {option_name}<br>Selection: {selection}<br>{extra}</font></td><td></td><td></td></tr>")
    return row + info, total


def totals_rows(subtotal, tax):
    rows = [("Subtotal:", money(subtotal)), ("GST/HST&nbsp;Tax&nbsp;Total:", money(tax)),
            ("PST&nbsp;Tax&nbsp;Total:", "$0.00"), ("Total:", f"<b>{money(subtotal + tax)}</b>")]
    return "\n".join(f'<tr><td></td><td></td><td></td><td align="right" colspan="2">{FONT}<b>{label}&nbsp;</b></font></td>'
                     f'<td align="right">{FONT}{value}&nbsp;</font></td></tr>' for label, value in rows)


def po_html(h, po):
    body, subtotal = "", Decimal(0)
    for line in po["lines"]:
        text, total = line_rows(line, h["plan"].split(" - ")[-1])
        body, subtotal = body + text, subtotal + total
    tax = subtotal * GST
    if tax != tax.quantize(CENT):
        sys.exit(f"{po['number']}: subtotal {subtotal} gives GST {tax}, not whole cents. Change a quantity.")
    city = "Sampleton, AB&nbsp;&nbsp;T0X 0X0"
    job_name = f"{h['job']}-{h['address']}"
    head = (f'<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
            f"<title>BuildPro:  Job Management</title></head>\n<body bgcolor=\"white\">\n"
            f"<!-- MADE-UP PRACTICE DOCUMENT. Not a real purchase order. Laid out like a BuildPro PO print. -->\n"
            f'<table width="660" align="center" border="1"><tr><td bgcolor="#f7f3f7"><table width="660"><tr>'
            f'<td width="200">{FONT}<b>{h["community"]}&nbsp;</b></font></td>'
            f'<td width="260" align="center"><font face="arial" style="font-size:15px;"><b>{BUILDER}</b><br>'
            f"<b>Purchase Order Request</b></font><table>"
            f'<tr><td>{FONT}<b>ORDER #:</b></font></td><td align="right">{FONT}&nbsp;{po["number"]}&nbsp;</font></td></tr>'
            f'<tr><td>{FONT}<b>COST CODE:</b></font></td><td align="right">{FONT}&nbsp;{po["cost_code"]}&nbsp;</font></td></tr>'
            f'</table></td><td width="200" align="right">{FONT}[practice copy]</font></td></tr></table></td></tr></table>\n')
    contact = ('<table width="660" align="center"><tr><td><b>CONTACT INFORMATION:</b></td></tr></table>\n'
               '<table width="660" align="center" border="2" rules="none"><tr><td valign="top"><table width="325">'
               + pair("FROM", f"{BUILDER} - {h['community']}") + pair("ADDRESS", f"100 Example Way<br>{city}")
               + pair("MAIN", "5555555555") + '</table></td><td valign="top"><table width="325">'
               + pair("TO", VENDOR[0]) + pair("ATTN", "Office") + pair("OFFICE", "5555555555")
               + pair("VENDOR #", VENDOR[1]) + "</table></td></tr></table>\n")
    job = ('<table width="660" align="center"><tr><td><b>JOB INFORMATION:</b></td></tr></table>\n'
           '<table width="660" align="center" border="2" rules="none"><tr><td valign="top"><table width="325">'
           + pair("JOB NAME", html.escape(job_name)) + pair("JOB ADDRESS", f"{html.escape(h['address'])}<br>{city}")
           + pair("DATE NEEDED", f"<b>{po['needed']}</b>") + pair("PRICE EFFECTIVE DATE", po.get("price_date", DEFAULT_PRICE_DATE))
           + '</table></td><td valign="top"><table width="325">' + pair("PLAN", h["plan"])
           + pair("ELEV/SWING", h["elevation"]) + pair("LOT/BLOCK/UNIT", f"{h['lot']}/{h['block']}/")
           + "</table></td></tr></table>\n"
           f'<table width="660" align="center"><tr><td>{FONT}Please direct questions regarding the following tasks to: '
           f"Purchasing Desk. EMAIL: purchasing@samplebuilder.example</font></td></tr></table>\n")
    detail = ('<table width="660" align="center"><tr><td><b>PURCHASE ORDER DETAIL:</b></td></tr></table>\n'
              '<table width="660" align="center" border="1"><tr><td><table width="660">\n'
              f"<tr><th>{FONT}<u>OPTION NO.</u></font></th><th align=\"left\">{FONT}<u>SKU No.&nbsp;&nbsp;DESCRIPTION</u></font></th>"
              f'<th align="right">{FONT}<u>UOM</u></font></th><th align="right">{FONT}<u>QTY</u></font></th>'
              f'<th align="right">{FONT}<u>UNIT PRICE</u></font></th><th>{FONT}<u>TOTAL</u></font></th></tr>\n'
              + body + totals_rows(subtotal, tax)
              + f'\n<tr><td>{FONT}<b>Approved&nbsp;By</b></font></td><td align="right">{FONT}<b>Date</b></font></td><td></td></tr>\n'
              "</table></td></tr></table>\n")
    foot = (f'<table width="660" align="center"><tr><td align="left">{FONT}Submitted by:&nbsp;Purchasing Desk</font></td>'
            f'<td align="right">{FONT}{po["submitted"]}</font></td></tr></table>\n</body></html>\n')
    return head + contact + job + detail + foot


def epo_html(h, e):
    rows = [("EPO NAME", e["name"]), ("JOB", f"{h['job']}-{h['address']}"), ("LOT/BLOCK", f"{h['lot']}/{h['block']}"),
            ("TRADE PARTNER", VENDOR[0]), ("ACCOUNT CODE", e["account"]), ("REASON CODE", e["reason"]),
            ("NOTES", e["notes"]), ("EPO TOTAL", f"${Decimal(e['total']):.2f}"), ("DATE REQUESTED", e["requested"]),
            ("APPROVAL STATUS", "Approved")]
    cells = "\n".join(f"<tr><td><b>{k}</b></td><td>{html.escape(v)}</td></tr>" for k, v in rows)
    return ('<html><head><meta charset="utf-8"><title>BuildPro: EPO</title></head>\n'
            "<body><!-- MADE-UP PRACTICE DOCUMENT. Not a real EPO. -->\n"
            f'<h3>{BUILDER} - Extra Purchase Order</h3>\n<table border="1" cellpadding="4" cellspacing="0">\n'
            f"{cells}\n</table></body></html>\n")


def house_info(h):
    return (f"# House info\n\nMade-up practice house. Not a real job.\n\n- Address: {h['address']}\n"
            f"- Lot: {h['lot']}, block {h['block']}\n- Builder: {BUILDER}\n"
            f"- Date measured: {h['measured']}\n- Date dropped in: {h['dropped']}\n")


def sam_answers(h):
    lines = [f"# {h['address']}: Sam's answers", "",
             "Whoever plays Sam gives these answers, only when the folder asks. Anything it asks that is",
             "not below: answer \"I don't know\", and note the question as a finding.", ""]
    lines += [f"- **{when}:** \"{answer}\"" for when, answer in h["sam_answers"]]
    return "\n".join(lines) + "\n"


def notes_form(h):
    return h.get("notes_form", "typed")


def notes_text(h):
    """What Sam's notes say, as text: typed notes as written, a voice memo as he meant it, a photo
    as the page reads with crossed-out words dropped. The answer key is checked against this."""
    if notes_form(h) == "photo":
        return "\n".join(handwriting.plain_text(p) for p in h["photos"])
    if notes_form(h) == "voice":
        return h["notes_meant"]
    return h.get("notes_meant", h["notes"])


def write_notes(h, folder):
    """Typed notes as site-notes.txt, a voice memo as the phone transcribed it, or photo pages."""
    for old in list(folder.glob("site-notes*")) + list(folder.glob("voice-memo*")):
        old.unlink()
    if notes_form(h) == "photo":
        for number, page in enumerate(h["photos"], start=1):
            handwriting.draw_page(page, f"{h['slug']}-{number}", folder / f"site-notes-photo-{number}.jpg")
    elif notes_form(h) == "voice":
        (folder / "voice-memo-transcript.txt").write_text(h["notes"], encoding="utf-8", newline="\n")
    else:
        (folder / "site-notes.txt").write_text(h["notes"], encoding="utf-8", newline="\n")


def write_house(h):
    folder = HERE / h["slug"] / "intake"
    folder.mkdir(parents=True, exist_ok=True)
    for po in h["pos"]:
        name = f"PO {po['number'].replace('/', '-')}.html"
        (folder / name).write_text(po_html(h, po), encoding="utf-8", newline="\n")
    for e in h["epos"]:
        (folder / e["file"]).write_text(epo_html(h, e), encoding="utf-8", newline="\n")
    write_notes(h, folder)
    (folder / "house-info.md").write_text(house_info(h), encoding="utf-8", newline="\n")
    (HERE / h["slug"] / "sam-answers.md").write_text(sam_answers(h), encoding="utf-8", newline="\n")
    return folder


def main():
    spec = json.loads((HERE / "houses.json").read_text(encoding="utf-8"))
    for h in spec["houses"]:
        print("wrote", write_house(h).relative_to(HERE.parent.parent))


if __name__ == "__main__":
    main()
