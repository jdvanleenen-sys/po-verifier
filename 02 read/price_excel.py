"""The price list's Excel file, turned into the plain text the rest of the folder reads.

Sam keeps his price list in reference/price-list.xlsx, on a sheet named "Price list", with the
columns Item, Unit, Rate, Active first. Any column after those (such as Source) is his and is
ignored. prices.py reads the text this module makes, checks it, and freezes it per house as a CSV,
so a later change in Excel never changes a house already checked.
"""
import csv
import io
import sys
from decimal import Decimal

SHEET = "Price list"
COLUMNS = 4


def cell_text(value):
    """A cell as the CSV would hold it: TRUE/FALSE, a rate without float noise, or the text."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(Decimal(repr(value)))
    return str(value)


def open_sheet(path):
    try:
        from openpyxl import load_workbook
    except ImportError:
        sys.exit("Reading the Excel price list needs openpyxl. Install it with: python -m pip install openpyxl")
    if not path.exists():
        sys.exit(f"The price list was not found at {path}. It must be an Excel file named price-list.xlsx "
                 "in the reference folder.")
    book = load_workbook(path, read_only=True, data_only=True)
    if SHEET not in book.sheetnames:
        sys.exit(f"The price list workbook has no sheet named '{SHEET}' (it has: {', '.join(book.sheetnames)}). "
                 f"Rename the sheet with the rates to '{SHEET}'.")
    return book[SHEET]


def workbook_csv(path):
    """The 'Price list' sheet's first four columns as UTF-8 CSV bytes, empty rows left out."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    for row in open_sheet(path).iter_rows(values_only=True):
        cells = [cell_text(v) for v in (list(row) + [None] * COLUMNS)[:COLUMNS]]
        if any(c.strip() for c in cells):
            writer.writerow(cells)
    return out.getvalue().encode("utf-8")


def write_workbook(csv_raw, path):
    """Write CSV price rows (Item, Unit, Rate, Active) as an Excel price list. For tests and setup."""
    from openpyxl import Workbook
    book = Workbook()
    sheet = book.active
    sheet.title = SHEET
    rows = list(csv.reader(io.StringIO(csv_raw.decode("utf-8-sig"))))
    sheet.append(rows[0])
    for item, unit, rate, active in rows[1:]:
        sheet.append([item, unit, Decimal(rate.replace("$", "").replace(",", "")) if rate.strip() else None,
                      active.strip().lower() in ("true", "yes", "y", "1", "x")])
    book.save(path)
