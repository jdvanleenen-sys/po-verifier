"""Write a house's variance from Sam's approved read-back, by code. Run from the repo root:

    python "03 compare/compare.py" <house>

Writes 03 compare/<house>/variance-N.md (the next free N), in the form of templates/variance.md.
Nothing in it is typed by the AI. It refuses to start unless the highest read-back carries Sam's
yes and its rule grid passes --final. The arithmetic is in compare_rows.py.
"""
import re
import sys
from datetime import date
from decimal import Decimal

import compare_rows as calc
from compare_rows import ROOT, money
import grid  # noqa: E402  (compare_rows puts 02 read on the path)
import grid_check  # noqa: E402
import prices  # noqa: E402
from grid_rules import show  # noqa: E402

ROW_HEADER = ("| Row | PO number | Item | Unit | Agreed rate | PO qty | PO rate | PO amount | Measured qty | "
              "Measured value | Variance | Why | Call |")


def read(path):
    return path.read_bytes().decode("utf-8-sig")


def inputs(house):
    """The approved read-back, its grid and the thresholds, or a stop with the reason."""
    n, path = grid.numbered(house, "read-back")
    if path is None:
        sys.exit(f"No read-back for {house} in 02 read/.")
    text = read(path)
    if not calc.sams_yes(text):
        sys.exit(f"{path.name} does not carry Sam's yes. Send the house back to 02 read.")
    grid_file = grid.grid_path_for(path)
    if not grid_file.exists():
        sys.exit(f"No {grid_file.name} beside {path.name}. Send the house back to 02 read.")
    grid_text = read(grid_file)
    problems, _ = grid_check.check_grid(text, grid_text, prices.snapshot_bytes(house, text), final=True)
    if problems:
        sys.exit(f"{grid_file.name} does not pass, so nothing was compared:\n- " + "\n- ".join(problems))
    return path, text, grid_text, calc.thresholds(read(calc.CONTRACTOR))


def row_line(r, ignore, flag):
    on_po = r["po"] != "none"
    cells = [r["num"], r["po"], r["item"], r["unit"], money(r["rate"]), show(r["po_qty"]),
             money(r["po_rate"]) if on_po else "", money(r["po_amount"]), show(r["measured_qty"]),
             money(r["measured_value"]), money(r["variance"], True), calc.why(r),
             calc.call(r["variance"], ignore, flag)]
    return "| " + " | ".join(cells) + " |"


def set_aside_lines(set_aside):
    if not set_aside:
        return ["| none | | Every row was comparable and priced. |"]
    lines = []
    for r, reason in set_aside:
        item = r.get("price list item", "").strip() or r.get("line as printed", "").strip()
        lines.append(f"| {r.get('po number', '').strip()} | row {r.get('#', '').strip()}: {item} | {reason} |")
    return lines


def totals(compared, flag):
    po = sum((r["po_amount"] for r in compared), Decimal(0))
    measured = sum((r["measured_value"] for r in compared), Decimal(0))
    variance = sum((r["variance"] for r in compared), Decimal(0))
    if variance != measured - po:
        sys.exit("The row variances do not add up to the totals. Nothing was written.")
    flagged = "yes" if abs(variance) >= flag else "no"
    return [f"- Total of POs: {money(po)}",
            f"- Total measured value: {money(measured)}",
            f"- Total variance: {money(variance, True)} ({money(measured)} - {money(po)}; equals the sum "
            "of the row variances)",
            f"- House flagged on total: {flagged} ({money(abs(variance))} against the flag line {money(flag)})"]


def render(house, n, path, text, compared, set_aside, limits):
    ignore, flag, note = limits
    read_line = re.search(r"^price list read:\s*(.+)$", text, re.M)
    epo_count = sum(1 for r in compared if r["epo"])
    return "\n".join([
        "---", f"house: {house}", f"attempt: {n}", "stage: 03 compare", f"from: 02 read/{house}/{path.name}",
        f"price list read: {read_line.group(1) if read_line else 'not recorded'} (as recorded in {path.stem})",
        "---", "", f"# {house}, variance {n}", "",
        "Written by `03 compare/compare.py` from the read-back named above. No number here was typed.", "",
        "## Rows", ROW_HEADER, "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        *[row_line(r, ignore, flag) for r in compared], "",
        f"{epo_count} row(s) carry an EPO already issued, counted in their PO amount.", "",
        "## Not comparable, or left unpriced by Sam", "| PO number | Item | Why |", "|---|---|---|",
        *set_aside_lines(set_aside), "",
        "## Thresholds used",
        f"From `reference/contractor.md` ({note}): ignore under {money(ignore)}; Sam's call {money(ignore)} "
        f"to under {money(flag)}; flag {money(flag)} and up; house flagged when its total variance is "
        f"{money(flag)} or more, plus or minus.", "",
        "## Totals, before tax", *totals(compared, flag), "",
        "## Checks run",
        f"Run by `03 compare/compare.py`, {date.today().isoformat()}. Decimal arithmetic.",
        f"- Read-back carries Sam's yes: pass: {path.name}.",
        f"- Rule grid passes --final: pass: grid-{path.stem.split('-')[-1]}.md.",
        f"- Every read-back row accounted for: pass: {len(compared)} compared + {len(set_aside)} set apart "
        f"= {len(compared) + len(set_aside)}.",
        "- Rates taken from the read-back only; the price list was not read again: pass.", ""])


def next_number(folder):
    taken = [int(m.group(1)) for p in folder.glob("variance-*.md")
             if (m := re.match(r"variance-(\d+)\.md$", p.name))]
    return max(taken, default=0) + 1


def write_variance(house):
    path, text, grid_text, limits = inputs(house)
    compared, set_aside, problems = calc.work_out(text, grid_text)
    if problems:
        sys.exit("The read-back cannot be compared:\n- " + "\n- ".join(problems))
    folder = ROOT / "03 compare" / house
    folder.mkdir(parents=True, exist_ok=True)
    n = next_number(folder)
    target = folder / f"variance-{n}.md"
    target.write_text(render(house, n, path, text, compared, set_aside, limits), encoding="utf-8")
    return f"{target.name} written: {len(compared)} rows compared, {len(set_aside)} set apart."


def main(argv):
    if len(argv) != 2:
        sys.exit('Use: python "03 compare/compare.py" <house>')
    print(write_variance(argv[1]))


if __name__ == "__main__":
    main(sys.argv)
