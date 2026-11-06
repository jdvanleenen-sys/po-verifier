"""Write each PO style's intake files from styles.json. Run from the repo root:

    python tests/po-styles/make_styles.py

For each style it writes tests/po-styles/<slug>/intake/: the PO printed to PDF in that builder's
own layout, Sam's site notes, house-info.md; and tests/po-styles/<slug>/sam-answers.md. A style
with "pdf" (the peer tester's house) keeps its own PDFs, copied from tests/po-styles/<slug>/source/.
Needs Chrome or Edge (05 request/printing.py finds it).
"""
import html
import json
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pipeline  # noqa: E402  (puts 05 request on the path)
import printing  # noqa: E402

STYLE = ("body{font-family:Arial,Helvetica,sans-serif;font-size:11px;margin:28px}"
         "table{border-collapse:collapse;width:100%;margin-top:10px}td,th{border:1px solid #999;padding:4px;text-align:left}"
         "th{background:#eee}.r{text-align:right}h1{font-size:18px;margin:0 0 6px}.head td{border:none;padding:2px 8px 2px 0}")


def fmt(value, style, credit=False):
    """An amount the way this builder prints it."""
    v = Decimal(value)
    kind = style["layout"].get("money", "dollar")
    if kind == "fr":
        whole, cents = f"{abs(v):,.2f}".split(".")
        text = whole.replace(",", " ") + "," + cents + " $"
        return ("-" + text) if v < 0 else text
    if kind == "plain":
        return f"{abs(v):,.2f} CR" if v < 0 else f"{v:,.2f}"
    if style["layout"].get("credit") == "parens" and v < 0:
        return f"(${abs(v):,.2f})"
    return f"-${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"


def cell(key, line, po, style):
    amount = Decimal(line["qty"]) * Decimal(line["price"])
    taxes = " + ".join(f"{label} {pct}%" for label, pct in po["taxes"])
    values = {"sku": line.get("sku", line["ref"]), "ref": line["ref"], "desc": line["desc"], "unit": line["unit"],
              "qty": line["qty"], "received": "0", "option": line.get("option", ""), "markup": line.get("markup", ""),
              "price": fmt(line.get("printed_price", line["price"]), style), "amount": fmt(amount, style),
              "printed_price": fmt(line.get("printed_price", line["price"]), style), "retainage": "10%", "taxrate": taxes}
    if style["layout"].get("money") == "fr":
        values["qty"] = line["qty"].replace(".", ",")
    return html.escape(values[key])


def lines_table(po, style):
    cols = style["layout"]["cols"]
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in cols)
    body = "".join("<tr>" + "".join(f"<td>{cell(k, l, po, style)}</td>" for k, _ in cols) + "</tr>" for l in po["lines"])
    return f"<table><tr>{head}</tr>{body}</table>"


def totals(po, style):
    subtotal, taxes, total = pipeline.po_sums(po)
    rows = [("Subtotal", fmt(subtotal, style))]
    if style["layout"].get("inclusive"):
        rows += [(f"Includes {label} {pct.normalize():f}%", fmt((subtotal * pct / (100 + pct)).quantize(pipeline.CENT), style))
                 for label, pct, _ in taxes]
        rows.append(("Total", fmt(subtotal, style)))
    else:
        rows += [(f"{label} ({pct.normalize():f}%)", fmt(t, style)) for label, pct, t in taxes]
        rows.append(("Total", fmt(total, style)))
    rows += [(label, fmt(v, style)) for label, v in style["layout"].get("after_total", [])]
    return "<table style='width:45%;margin-left:55%'>" + "".join(
        f"<tr><td>{html.escape(k)}</td><td class='r'>{html.escape(v)}</td></tr>" for k, v in rows) + "</table>"


def header(style, numbers):
    lay = style["layout"]
    pairs = [(lay["po_label"], numbers), ("Builder", style["builder"]), ("Vendor", f"{style['painter']} {style['vendor_no']}".strip())]
    pairs += [tuple(p) for p in lay["head"]]
    rows = "".join(f"<tr><td><b>{html.escape(k)}:</b></td><td>{html.escape(v)}</td></tr>" for k, v in pairs)
    return f"<h1>{html.escape(lay['title'])}</h1><table class='head'>{rows}</table>"


def po_html(style, pos):
    numbers = " / ".join(p["number"] for p in pos)
    parts = [header(style, numbers)]
    for po in pos:
        if len(pos) > 1 or po.get("title_note"):
            parts.append(f"<h3>{html.escape(po['number'])} {html.escape(po.get('title_note', ''))}</h3>")
        parts += [lines_table(po, style), totals(po, style)]
    for e in style.get("epos", []):
        if e["against"] in [p["number"] for p in pos]:
            parts.append(f"<h3>EPO {html.escape(e['name'])} against {html.escape(e['against'])}</h3>"
                         f"<p>{html.escape(e['note'])} Total: {fmt(e['total'], style)}</p>")
    return f"<html><head><meta charset='utf-8'><style>{STYLE}</style></head><body>{''.join(parts)}</body></html>"


def documents(style):
    """[(file name, the POs on it)]: one PDF per PO, or one for all when the builder prints them together."""
    if style["layout"].get("combined"):
        return [(f"PO {' + '.join(p['number'] for p in style['pos'])}.pdf", style["pos"])]
    return [(f"PO {p['number'].replace('/', '-')}.pdf", [p]) for p in style["pos"]]


def site_notes(style):
    lines = [f"{style['painter']} - site notes", f"Measured {style['measured']}", ""]
    rows = pipeline.rows_of(style)
    return "\n".join(lines + [f"- {r['words']}" for r in rows if r.get("measured") is not None]) + "\n"


def house_info(style):
    lot = f"- Lot: {style['lot']}\n" if style["lot"] else ""
    return (f"# House info\n\nMade-up practice house. Not a real job.\n\n- Address: {style['address']}\n{lot}"
            f"- Builder: {style['builder']}\n- Date measured: {style['measured']}\n- Date dropped in: 2026-11-05\n")


def sam_answers(style):
    rows = pipeline.rows_of(style)
    on = [f"row {r['num']} ({r['item']}, {r['ref'] or 'no PO'})" for r in rows if int(r["num"]) in style["on"]]
    asides = [f"- **If it asks about {r['ref']} {r['desc']}:** \"{r['why'].capitalize()}. Don't compare it.\""
              for r in rows if r.get("cmp") is False]
    return "\n".join([
        f"# {style['slug']}: Sam's answers", "",
        f"Sam is {style['painter'].rstrip('.')}. Whoever plays Sam gives these answers, only when asked. Anything else: "
        "\"I don't know\", and note the question as a finding.", "",
        "- **When it shows the read-back table:** \"Yes, to the whole table.\"",
        f"- **At review:** \"Put on {', '.join(on)}. Leave the rest off. Yes, to the table with those decisions.\"",
        *asides, *[f"- {a}" for a in style.get("answers", [])],
        "- **If it asks about markup:** \"The builder pays the price with the markup. That's the PO price.\"",
        "- **If it asks whether the prices include tax:** \"" + ("Yes, the tax is in the prices." if style.get("layout", {}).get("inclusive")
                                                                  else "No, tax is on its own line.") + "\"",
        "- **If it asks whether to attach your site notes:** \"Yes, attach them.\"",
        "- **When it asks if this is the request he will send:** \"Yes, but this is practice. Write sent: no.\"", ""])


def write_style(style, browser):
    folder = HERE / style["slug"]
    intake = folder / "intake"
    if intake.exists():
        shutil.rmtree(intake)
    intake.mkdir(parents=True)
    (intake / "house-info.md").write_text(house_info(style), encoding="utf-8", newline="\n")
    (folder / "sam-answers.md").write_text(sam_answers(style), encoding="utf-8", newline="\n")
    if style.get("pdf"):
        for name in style["pdf"].values():
            shutil.copy(folder / "source" / name, intake / name)
        return
    (intake / "site-notes.txt").write_text(site_notes(style), encoding="utf-8", newline="\n")
    with tempfile.TemporaryDirectory() as tmp:
        for name, pos in documents(style):
            page = Path(tmp) / "po.html"
            page.write_text(po_html(style, pos), encoding="utf-8")
            printing.print_pdf(browser, page, intake / name)


def main():
    styles = json.loads((HERE / "styles.json").read_text(encoding="utf-8"))["styles"]
    browser = printing.find_browser()
    for style in styles:
        write_style(style, browser)
        print(f"{style['slug']}: written")


if __name__ == "__main__":
    main()
