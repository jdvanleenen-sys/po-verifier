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
MULTIPLIER_WORD = re.compile(r"\b(?:each|both|pairs?|double|twice|of them|times)\b|@|\(\s*\d+\s*\)|\b\d+\s+of\b",
                             re.I)
NUMBER_WORD = re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
                         r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b", re.I)
LOOSE_DIGIT = re.compile(r"(?<![/\d])\d")
EACH_SIDE = re.compile(r"\s*each\s+sides?\b", re.I)
RANGE = re.compile(r"\d\s*'?\s*(?:-|–|—|to)\s*\d", re.I)
POINTER = re.compile(r"\bsee\b|\bsame\b|\bditto\b|\bas above\b|\bdo\.(?!\w)|\brow\s*#?\s*\d", re.I)
FEET_INCHES = re.compile(r"\d\s*(?:'|ft\b|feet\b)\s*-?\s*\d+\s*(?:\"|in\b|inch)|\d\s*'\s*\d", re.I)
NO_NOTE = "done as ordered"
WORD_SIZE = re.compile(NUMBER_WORD.pattern + r"(?:[\s-]+[a-z]+)?\s*(?:'|ft\b|feet\b|foot\b|lf\b|sf\b|sq\b)", re.I)
WORD_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
STRAIGHT = str.maketrans({"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'",
                          "′": "'", "″": '"'})
JOINED = re.compile(r"(?<![\w.'])\d+\s*x(?=\s|$)|[+&*]|\([^)]*\d[^)]*\)", re.I)
CONFIRMED_N = re.compile(r",?\s*sam confirmed\s+(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)", re.I)


def straight(said):
    """Curly quotes as straight ones and prime marks as feet and inches, as typed on a phone or in Word."""
    return (said or "").translate(STRAIGHT)


def plain(number):
    return number.replace(",", "").lstrip("0") or "0"


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
    said = straight(said)
    confirmed = CONFIRMED_N.search(said)
    slot = (size_slot(said) or "").strip()
    found = SIZE_NUMBER.match(slot)
    if not found:
        return None
    after = slot[found.end():]
    unit = SIZE_UNIT.match(after)
    rest = after[unit.end():] if unit else after
    rest = CONFIRMED_N.sub("", rest) if confirmed else rest
    if EACH_SIDE.match(after) or not remark_ok(rest) or multiplied(rest):
        return None
    if words_multiply(said, found.group(1)) or words_disagree(said, found.group(1)):
        return None
    return found.group(1)


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
    if MULTIPLIER_WORD.search(words) or JOINED.search(words):
        return True
    return any(m.group(1).lstrip("0") != size.replace(",", "").lstrip("0") for m in TIMES.finditer(words))


def quoted(said):
    """Sam's own words: the first quoted phrase in the cell, or '' when there is none."""
    start = said.find('"')
    end = said.find('"', start + 1) if start >= 0 else -1
    return said[start + 1:end] if end > start else ""


def words_disagree(said, size):
    """Sam's quoted words do not back the size in the slot: they hold a range ('13-14''), a pointer
    ('see row 3', 'same as', 'ditto', 'as above'), feet and inches ('16 ft 6 in', '16'6"'), a number
    in words ('sixteen feet'), no number at all (other than the exact words 'done as ordered'), or
    numbers none of which is the slot's ('Railing 16'' with 61 in the slot). An item name may carry
    its own size ('8' doors x12'), so the slot only has to be one of his numbers."""
    if not size.strip("0.,"):
        return False  # a 0 already goes to Sam (size_doubt)
    confirmed = CONFIRMED_N.search(said)
    if confirmed and plain(confirmed.group(1)) == plain(size):
        return False  # Sam settled this exact number himself: "Sam confirmed 3016"
    words = quoted(said)
    if not words.strip() or words.strip().lower() == NO_NOTE:
        return False  # no quoted words (the "stringers; 34 ft" form), or no note by standing answer
    if RANGE.search(words) or POINTER.search(words) or FEET_INCHES.search(words) or WORD_SIZE.search(words):
        return True
    his = {n.replace(",", "").lstrip("0") or "0" for n in WORD_NUMBER.findall(words)}
    return not his or (size.replace(",", "").lstrip("0") or "0") not in his
