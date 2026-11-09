"""Reading Sam's size or count out of a read-back's "Sam measured" cell, by code. Used by grid_rules.

A cell is his words in quotes, then ';', then the size slot, then any notes. Only a size the code
can read exactly is a size; anything else is None, and the grid asks Sam.
"""
import re

SIZE_NUMBER = re.compile(r"(?:count\s+)?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)", re.I)
SIZE_UNIT = re.compile(r"\s*(?:'|(?:ft|feet|lf|sf|sq\.?\s?ft|ea|each)\b)", re.I)
NOT_A_REMARK = re.compile(r"(?:\d|x\b|x\s*\d|by\b|in\b|inch|to\b|or\b|and\b|plus\b|[+&\-'\"()/×½¼¾–—])", re.I)
WORDS_ONLY = re.compile(r"\s+[a-z][a-z ]*", re.I)


def size_slot(text):
    """The ';' part after Sam's first quoted phrase, or else the second ';' part: his size or count."""
    if '"' in text:
        start = text.index('"')
        end = text.find('"', start + 1)
        if end < 0:
            return None
        parts = text[end + 1:].split(";")
        return parts[1] if not parts[0].strip() and len(parts) > 1 else parts[0]
    parts = text.split(";")
    return parts[1] if len(parts) > 1 else None


def size_text(said):
    """Sam's size or count from the size slot (size_slot), or None so the grid asks Sam: one plain
    number, optionally "count " before it and a unit after it (', ft, feet, LF, SF, sq ft, EA,
    each), then only what remark_ok allows. His words are the FIRST quoted phrase, so a quoted
    source note later in the cell never moves where the size is read from."""
    slot = (size_slot(said or "") or "").strip()
    found = SIZE_NUMBER.match(slot)
    if not found:
        return None
    rest = slot[found.end():]
    unit = SIZE_UNIT.match(rest)
    rest = rest[unit.end():] if unit else rest
    return found.group(1) if remark_ok(rest) else None


def remark_ok(rest):
    """An allowlist of what may follow the size: nothing, a comma and a remark, or words with no
    number or sign before the first comma. " (x2)", " ×2", " – 14 ft", " ½ ft" are refused."""
    head, comma, tail = rest.partition(",")
    if head.strip() and not (WORDS_ONLY.fullmatch(head) and not NOT_A_REMARK.match(head.strip())):
        return False
    return not (comma and NOT_A_REMARK.match(tail.strip()))


