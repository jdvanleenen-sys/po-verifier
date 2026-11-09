"""Reading Sam's records: Markdown tables, cells, amounts and his approval. Used by money.py."""
import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02 read"))
from seal import approval_problems, read_record  # noqa: E402

AMOUNT = re.compile(r"(\(?)([+\-−]?)\s*\$?\s*(\d[\d,]*(?:\.\d+)?)")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def read_text(path):
    """Read a record written by any editor: UTF-8 with or without a BOM, or UTF-16. Anything else
    stops in plain words (seal.read_record), never a traceback."""
    return read_record(path)


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
    """A record counts only when sealed by 02 read/seal.py after Sam's plain yes, and unchanged since."""
    return not approval_problems(text)


TAX_NAME = re.compile(r"\b(gst/hst|hst|gst|pst|qst)\b", re.I)


def tax_names(read_back_text):
    """{PO number, lower case: the names of the taxes it charges (a non-zero amount)}, read from the
    read-back's POs read table: 'GST/HST $0.00; PST $342.19' gives {'pst'}."""
    out = {}
    for r in section(tables(read_back_text), "pos read"):
        po = column(r, "po number").strip().lower()
        for part in column(r, "tax lines").split(";"):
            names, amount = [n.lower() for n in TAX_NAME.findall(part)], to_amount(part)
            if po and names and amount:
                out.setdefault(po, set()).update(names)
    return out


DECISION = re.compile(r"^(on|off)(?:\s+\(.*\))?$", re.I)


def decision_word(cell):
    """Sam's review decision: 'on' or 'off' when the cell is exactly that word, alone or followed by a
    remark in brackets ("off (Sam: leave the doors off)"). Anything else, blank included, is None."""
    found = DECISION.match((cell or "").strip())
    return found.group(1).lower() if found else None


def decision_problem(cell):
    """Why a review decision cell is not a decision, in words Sam can act on."""
    said = (cell or "").strip()
    if not said:
        return "has no on/off decision from Sam. A blank is not a decision: ask him on or off"
    return (f"has no on/off decision from Sam: '{said}' is not on or off. Write exactly on or off, with any "
            "remark in brackets after it; ask Sam if he has not decided")
