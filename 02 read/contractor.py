"""Who this folder is for, read from reference/contractor.md, and the check that every PO is his.

One folder holds one contractor (CONTEXT.md). A PO made out to another vendor is another
contractor's house: it belongs in another copy of the folder, set up through 00 setup.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUP = ROOT / "reference" / "contractor.md"
VENDOR = re.compile(r"\(vendor\s+([^)]+)\)", re.I)
NO_VENDOR = ("none", "no vendor number", "")


def answer(text, question):
    """The answer cell of the setup table row that starts with these words."""
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower().startswith(question.lower()):
            return cells[1]
    return ""


def read(path=SETUP):
    """{"name", "vendor", "builders", "shown"}: shown is how the request prints the contractor."""
    text = Path(path).read_text(encoding="utf-8-sig") if Path(path).is_file() else ""
    business = answer(text, "Business")
    found = VENDOR.search(business)
    name = business[:found.start()].strip() if found else business.split(".")[0].strip()
    vendor = found.group(1).strip() if found else ""
    vendor = "" if vendor.lower() in NO_VENDOR else vendor
    builders = answer(text, "Builders")
    return {"name": name, "vendor": vendor, "builders": builders,
            "shown": f"{name} ({vendor})" if vendor else name}


def po_vendors(read_back_text):
    """(PO number, vendor cell) for each row of the read-back's POs read table."""
    rows, header, inside = [], None, False
    for line in read_back_text.splitlines():
        if line.startswith("#"):
            inside = "pos read" in line.lower()
            header = None
            continue
        if not inside or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
        elif not all(set(c) <= set("-: ") for c in cells) and "vendor" in header:
            rows.append((cells[0], cells[header.index("vendor")] if len(cells) > header.index("vendor") else ""))
    return rows


def vendor_problems(read_back_text, setup=None):
    """Every PO made out to someone other than this folder's contractor."""
    setup = setup or read()
    if not setup["name"]:
        return ["reference/contractor.md names no business. Run 00 setup before any house."]
    problems = []
    for po, cell in po_vendors(read_back_text):
        if setup["vendor"]:
            ok = re.search(rf"(?<![\w-]){re.escape(setup['vendor'])}(?![\w-])", cell, re.I)
        else:
            ok = setup["name"].lower() in cell.lower()
        if not ok:
            problems.append(f"PO {po} is made out to '{cell}', but this folder is set up for {setup['shown']}: "
                            "a different contractor is a different copy of the folder, set up through 00 setup")
    return problems
