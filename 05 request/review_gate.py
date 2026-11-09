"""What the request build would refuse about a review, checked before seal.py seals it.

A review that build will always refuse uses up a number if it is sealed first (loop run 6,
2026-11-09). So seal.py asks this module, for a review only: its from: names a variance of this
house, the Date under Sam's yes is a real day not after today, and the money gate finds nothing
wrong with its decisions, items and EPO targets against the variance and read-back it comes from.
"""
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / "02 read")]

FROM = re.compile(r"^from:[ \t]*`?([^`\n]+?)`?[ \t]*$", re.M)
DAY = re.compile(r"^-\s*Date:[ \t]*(\d{4}-\d{2}-\d{2})[ \t]*$", re.M)
READ_BACK = re.compile(r"02 read/[^/\s`]+/(read-back-\d+\.md)")


def date_problems(text, today=None):
    """The Date under Sam's yes is a real calendar day and not after today. Its shape is checked by
    seal.yes_problems; a day that does not exist (2026-11-31) must never reach a traceback."""
    m = DAY.search(text or "")
    if not m:
        return []
    try:
        day = date.fromisoformat(m.group(1))
    except ValueError:
        return [f"has a Date under Sam's yes that is not a real day: '{m.group(1)}'. Write the date Sam "
                "said yes, as YYYY-MM-DD"]
    if day > (today or date.today()):
        return [f"has a Date under Sam's yes after today ({m.group(1)}). Write the date Sam said yes"]
    return []


def variance_named(text, house):
    """The variance file the review's from: names, or None when it names anything else."""
    m = FROM.search(text or "")
    named = m.group(1).strip().replace("\\", "/") if m else ""
    return named if re.fullmatch(rf"03 compare/{re.escape(house)}/variance-\d+\.md", named) else None


def money_problems(path, text, house, named):
    """What the money gate says about this review, read as if Sam's yes were already sealed."""
    import house_checks
    import money
    import seal
    variance = ROOT / named
    if not variance.is_file():
        return []  # chain.py names a missing from: file
    v_text = money.read_text(variance)
    m = READ_BACK.search(v_text)
    read_back = ROOT / "02 read" / house / m.group(1) if m else None
    if read_back is None or not read_back.is_file():
        return [f"comes from {named}, which names no read-back that exists"]
    rb_text = money.read_text(read_back)
    grid = read_back.with_name(read_back.name.replace("read-back-", "grid-", 1))
    texts = {"review": seal.seal_text(path.name, text), "variance": v_text, "read-back": rb_text,
             "grid": money.read_text(grid) if grid.is_file() else None,
             "price-list": money.prices.snapshot_bytes(house, rb_text)}
    _, found = money.expected_request(texts)
    setup = ROOT / "reference" / "contractor.md"
    found += house_checks.standing_epo_problems(texts["review"], setup.read_text(encoding="utf-8-sig")
                                                if setup.is_file() else "", rb_text)
    return [f"would be refused by the request: {p}" for p in found]


def problems(path, text, today=None):
    """Every reason build would refuse this review, worded to follow '<file> was not sealed. It ...'."""
    path = Path(path)
    house = path.parent.name
    out = date_problems(text, today)
    named = variance_named(text, house)
    if named is None:
        return out + [f"has a from: line that is not a variance of this house; a review comes from "
                      f"03 compare/{house}/variance-N.md"]
    if out:
        return out
    try:
        return money_problems(path, text, house, named)
    except ValueError as e:  # seal_text: the yes itself is not in order; seal.py says so in its own words
        return list(e.args[0]) if e.args and isinstance(e.args[0], list) else [str(e)]
