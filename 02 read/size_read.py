"""Reading Sam's size or count out of a read-back's "Sam measured" cell, by code. Used by grid_rules.

A cell is his words in quotes, then ';', then the size slot, then any notes. Only a size the code
can read exactly is a size; anything else is None, and the grid asks Sam.
"""
import re

SIZE_NUMBER = re.compile(r"(?:count\s+)?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)", re.I)
SIZE_UNIT = re.compile(r"\s*(?:'|(?:ft|feet|lf|sf|sq\.?\s?ft|ea|each)\b)", re.I)
NOT_A_REMARK = re.compile(r"(?:\d|x\b|x\s*\d|by\b|in\b|inch|to\b|or\b|and\b|plus\b|[+&\-'\"()/×½¼¾–—])", re.I)
WORDS_ONLY = re.compile(r"\s+[a-z][a-z ]*", re.I)
TIMES = re.compile(r"(?<![a-z])[x×]\s*(\d+(?:\.\d+)?)(?![\d.]|\s*(?:'|\"|ft\b|feet\b|in\b))", re.I)
MULTIPLIER_WORD = re.compile(r"\b(?:each|both|pairs?|double|twice|of them)\b", re.I)
NUMBER_WORD = re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
                         r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b", re.I)
LOOSE_DIGIT = re.compile(r"(?<![/\d])\d")
EACH_SIDE = re.compile(r"\s*each\s+sides?\b", re.I)


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
    after = slot[found.end():]
    unit = SIZE_UNIT.match(after)
    rest = after[unit.end():] if unit else after
    if EACH_SIDE.match(after) or not remark_ok(rest) or multiplied(rest):
        return None
    return None if words_multiply(said or "", found.group(1)) else found.group(1)


def remark_ok(rest):
    """An allowlist of what may follow the size: nothing, a comma and a remark, or words with no
    number or sign before the first comma. " (x2)", " ×2", " – 14 ft", " ½ ft" are refused."""
    head, comma, tail = rest.partition(",")
    if head.strip() and not (WORDS_ONLY.fullmatch(head) and not NOT_A_REMARK.match(head.strip())):
        return False
    return not (comma and NOT_A_REMARK.match(tail.strip()))




def multiplied(rest):
    """The remark after the size counts something: x2, each, both sides, a pair, twice, two of them,
    a number in words, or a digit that is not part of a PO number such as /027."""
    return bool(TIMES.search(rest) or MULTIPLIER_WORD.search(rest) or NUMBER_WORD.search(rest)
                or LOOSE_DIGIT.search(rest))


def words_multiply(said, size):
    """Sam's quoted words multiply the size: '10' x2', 'each side', 'a pair'. 'x12' where 12 is the
    size itself is how he writes a count, not a multiplier."""
    start = said.find('"')
    end = said.find('"', start + 1) if start >= 0 else -1
    words = said[start + 1:end] if end > start else ""
    if MULTIPLIER_WORD.search(words):
        return True
    return any(m.group(1).lstrip("0") != size.replace(",", "").lstrip("0") for m in TIMES.finditer(words))
