"""The price list: one file, read by code, frozen per read-back.

The price list is reference/price-list.xlsx, kept by Sam in Excel (see price_excel.py). Nobody
else changes it.

  python "02 read/prices.py" snapshot <house>
      Checks the price list, freezes it as plain text in 02 read/<house>/price-list-N.csv
      (the next free N), and prints the line to put in the read-back's front matter:
      price list read: <date>, price-list-N.csv, sha256 <fingerprint>

  python "02 read/prices.py" check <house>
      Checks the highest-numbered read-back against the snapshot it names: the fingerprint, and
      every row's price list item, unit and rate. Run it before showing Sam the table.

The money gate (05 request/money.py) runs the same check before any request is numbered.
"""
import csv
import hashlib
import io
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import price_excel

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "reference" / "price-list.xlsx"
HEADER = ["item", "unit", "rate", "active"]
UNITS = {"Floor SF", "SF", "LF", "EA", "per room", "per kitchen", "Hours", "Incl."}
YES = {"true", "yes", "y", "1", "x"}
NO = {"false", "no", "n", "0", ""}
UNPRICED = "not on the price list"
PENDING = "pick one"
READ_LINE = re.compile(r"^price list read:\s*(.+)$", re.M)
SNAPSHOT_NAME = re.compile(r"price-list-\d+\.csv")
FINGERPRINT = re.compile(r"sha256\s+([0-9a-f]{64})")


def source_bytes(path=SOURCE):
    """The price list as the CSV text every check reads, made from the Excel file."""
    return price_excel.workbook_csv(path)


def fingerprint(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    """Excel saves UTF-8 with a BOM; older Excel saves Windows-1252. Accept both."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def to_rate(cell):
    """A rate as Excel may save it: 2.75, $2.75, 1,000 or $1,000.00. Anything else is None."""
    text = cell.strip().replace("$", "").replace(",", "")
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    return value if value >= 0 else None


def check_row(n, cells, problems):
    """One CSV row as a price row, or None with the problem written down."""
    if len(cells) != 4:
        problems.append(f"price list line {n}: {len(cells)} columns, not 4 (Item, Unit, Rate, Active)")
        return None
    item, unit, rate_cell, active_cell = (c.strip() for c in cells)
    rate, active = to_rate(rate_cell), active_cell.lower()
    if not item:
        problems.append(f"price list line {n}: no Item")
    elif unit not in UNITS:
        problems.append(f"price list line {n} ({item}): unit '{unit}' is not one of {sorted(UNITS)}")
    elif rate is None:
        problems.append(f"price list line {n} ({item}): rate '{rate_cell}' is not a number")
    elif active not in YES | NO:
        problems.append(f"price list line {n} ({item}): Active '{active_cell}' is not TRUE or FALSE")
    else:
        return {"item": " ".join(item.split()), "unit": unit, "rate": rate, "active": active in YES}
    return None


def parse(raw):
    """Every price row and every problem in a price list file. A problem stops the read."""
    text, problems, rows = decode(raw), [], {}
    lines = list(csv.reader(io.StringIO(text)))
    if not lines:
        return {}, ["the price list is empty"]
    header = [c.strip().lower() for c in lines[0]]
    if header != HEADER:
        if ";" in text.splitlines()[0]:
            problems.append("the price list was saved with semicolons. In Excel, save it as "
                            "'CSV UTF-8 (Comma delimited)'")
        else:
            problems.append(f"the price list's first line is {lines[0]}, not Item, Unit, Rate, Active")
        return {}, problems
    for n, cells in enumerate(lines[1:], start=2):
        if not any(c.strip() for c in cells):
            continue
        row = check_row(n, cells, problems)
        if row is None:
            continue
        key = row["item"].lower()
        if key in rows and rows[key]["active"] and row["active"]:
            problems.append(f"price list line {n}: '{row['item']}' is on the list twice as active")
        if key not in rows or row["active"]:
            rows[key] = row
    return rows, problems


def next_snapshot(folder):
    taken = [int(m.group(1)) for p in folder.glob("price-list-*.csv")
             if (m := re.match(r"price-list-(\d+)\.csv$", p.name))]
    return folder / f"price-list-{max(taken, default=0) + 1}.csv"


def snapshot(house):
    """Freeze the checked price list in the house's read folder. Returns the front-matter line."""
    raw = source_bytes()
    rows, problems = parse(raw)
    if problems:
        sys.exit("The price list has problems, so nothing was read. Ask Sam to fix them in Excel:\n- "
                 + "\n- ".join(problems))
    folder = ROOT / "02 read" / house
    folder.mkdir(parents=True, exist_ok=True)
    target = next_snapshot(folder)
    target.write_bytes(raw)
    active = sum(1 for r in rows.values() if r["active"])
    return (f"price list read: {date.today().isoformat()}, {target.name}, sha256 {fingerprint(raw)} "
            f"({len(rows)} rows, {active} active)")


def snapshot_named(read_back_text):
    """The snapshot file name and fingerprint the read-back's front matter gives, or None."""
    line = READ_LINE.search(read_back_text)
    if not line:
        return None, None
    name, print_ = SNAPSHOT_NAME.search(line.group(1)), FINGERPRINT.search(line.group(1))
    return (name.group(0) if name else None), (print_.group(1) if print_ else None)


def rows_table(read_back_text):
    """The read-back's Rows table as dicts keyed by exact lower-case header."""
    rows, header, inside = [], None, False
    for line in read_back_text.splitlines():
        if line.startswith("#"):
            inside, header = line.lstrip("#").strip().lower() == "rows", None
        elif inside and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if header is None:
                header = [c.lower() for c in cells]
            elif not all(set(c) <= set("-: ") for c in cells):
                rows.append(dict(zip(header, cells)))
    return rows


def check_read_back(read_back_text, snapshot_raw, pending_ok=False):
    """Every way the read-back's prices could disagree with the frozen price list.

    pending_ok: a row still waiting on Sam's "pick one" passes (at 02 read, before he answers).
    The money gate never passes one.
    """
    name, expected = snapshot_named(read_back_text)
    if not name or not expected:
        return ["the read-back's 'price list read:' line does not name a price-list-N.csv snapshot "
                "and its sha256 (run: python \"02 read/prices.py\" snapshot <house>)"]
    if snapshot_raw is None:
        return [f"the snapshot {name} named in the read-back is not in the house's 02 read folder"]
    if fingerprint(snapshot_raw) != expected:
        return [f"{name} has changed since the read-back was made (its sha256 does not match)"]
    prices, problems = parse(snapshot_raw)
    for r in rows_table(read_back_text):
        problems += check_price_row(r, prices, pending_ok)
    return problems


def check_price_row(r, prices, pending_ok=False):
    """One read-back row against the frozen list: exact item, its unit, its rate, and active."""
    num, item = r.get("#", "?"), " ".join(r.get("price list item", "").split())
    rate_cell = r.get("rate", "")
    if item.lower().startswith(PENDING):
        return [] if pending_ok else [f"read-back row {num}: still waiting on Sam's pick"]
    if item.lower().startswith(UNPRICED):
        return [] if not rate_cell.strip() else [f"read-back row {num}: unpriced, but has a rate"]
    match = prices.get(item.lower())
    if match is None:
        return [f"read-back row {num}: '{item}' is not on the price list snapshot"]
    if not match["active"]:
        return [f"read-back row {num}: '{item}' is not active on the price list"]
    found = []
    if r.get("unit", "").strip() != match["unit"]:
        found.append(f"read-back row {num}: unit '{r.get('unit', '')}', the price list says {match['unit']}")
    if to_rate(rate_cell) != match["rate"]:
        found.append(f"read-back row {num}: rate '{rate_cell}', the price list says {match['rate']}")
    return found


def latest_read_back(house):
    folder = ROOT / "02 read" / house
    found = [(int(m.group(1)), p) for p in folder.glob("read-back-*.md")
             if (m := re.match(r"read-back-(\d+)\.md$", p.name))]
    return max(found)[1] if found else None


def snapshot_bytes(house, read_back_text):
    name, _ = snapshot_named(read_back_text)
    path = ROOT / "02 read" / house / name if name else None
    return path.read_bytes() if path and path.is_file() else None


def main(argv):
    if len(argv) != 3 or argv[1] not in ("snapshot", "check"):
        sys.exit('Use: python "02 read/prices.py" snapshot|check <house>')
    house = argv[2]
    if argv[1] == "snapshot":
        print(snapshot(house))
        return
    path = latest_read_back(house)
    if path is None:
        sys.exit(f"No read-back for {house} in 02 read/.")
    text = path.read_bytes().decode("utf-8-sig")
    problems = check_read_back(text, snapshot_bytes(house, text), pending_ok=True)
    if problems:
        sys.exit(f"{path.name}: the prices do not match the price list:\n- " + "\n- ".join(problems))
    waiting = sum(1 for r in rows_table(text) if r.get("price list item", "").lower().startswith(PENDING))
    note = f" {waiting} row(s) wait on Sam's pick; the house cannot leave 02 read until he answers." if waiting else ""
    print(f"{path.name}: every priced row matches its price list snapshot exactly.{note}")


if __name__ == "__main__":
    main(sys.argv)
