"""Reading Sam's records: Markdown tables, cells, amounts and his approval. Used by money.py."""
import re
from decimal import Decimal
from pathlib import Path

AMOUNT = re.compile(r"(\(?)([+\-−]?)\s*\$?\s*(\d[\d,]*(?:\.\d+)?)")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def read_text(path):
    """Read a record written by any editor: UTF-8 with or without a BOM, or UTF-16."""
    raw = Path(path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def to_amount(cell):
    """The first money amount in a cell, signed: '+$426.00', '-$170.00', '($170.00)', '$1,000.00'."""
    match = AMOUNT.search(cell or "")
    if not match:
        return None
    value = Decimal(match.group(3).replace(",", ""))
    negative = match.group(1) == "(" or match.group(2) in ("-", "−")
    return -value if negative else value


def to_number(cell):
    """The first plain number in a cell: '6 + 2 on EPO 01' gives 6."""
    match = NUMBER.search(cell or "")
    return Decimal(match.group(0).replace(",", "")) if match else None


def tables(text):
    """Every Markdown table in a text, keyed by the section heading above it."""
    found, heading, rows = {}, "", None
    for line in text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
        elif line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if rows is None:
                rows = {"header": [c.lower() for c in cells], "rows": []}
                found.setdefault(heading, rows)
            elif not all(set(c) <= set("-: ") for c in cells):
                rows["rows"].append(dict(zip(rows["header"], cells)))
        else:
            rows = None
    return found


def column(row, *starts):
    """The cell whose header starts with any of the given words."""
    for key, value in row.items():
        if any(key.startswith(s) for s in starts):
            return value
    return ""


def section(found, *words):
    for heading, table in found.items():
        if all(w in heading for w in words):
            return table["rows"]
    return []


def approved(text):
    """A record counts only with status: approved and a yes written in Sam's yes block."""
    status = re.search(r"^status:\s*(\S+)", text, re.M)
    answer = re.search(r"^-\s*Answer:\s*(.+)$", text, re.M)
    return bool(status and status.group(1).lower() == "approved"
                and answer and re.search(r"\byes\b", answer.group(1), re.I) is not None)
