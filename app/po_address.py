"""The job address a PO prints, read by code so Lock can ask Sam about a mismatch before any read.
Only the street line under JOB ADDRESS: is used. A PO code cannot read (a photo) gives None, and is
left to the read stage."""
import html
import re
from pathlib import Path

TAG = re.compile(r"<[^>]+>")
DROP = re.compile(r"(?is)<(script|style)\b.*?</\1>")
JOB_ADDRESS = re.compile(r"JOB ADDRESS:\s*\|\s*([^|]+?)\s*\|")
WORDS = {"drive": "dr", "street": "st", "road": "rd", "avenue": "ave", "crescent": "cres", "terrace": "terr",
         "court": "ct", "boulevard": "blvd", "place": "pl", "lane": "ln", "way": "way", "bay": "bay",
         "close": "cl", "gate": "gt", "point": "pt", "trail": "tr", "heights": "hts", "circle": "cir"}


def _cells(text):
    """Page text with each cell boundary as ' | ', so a label and its value sit side by side."""
    text = TAG.sub(" | ", DROP.sub("", text))
    return re.sub(r"(\s*\|\s*)+", " | ", html.unescape(text))


def _pdf_text(path):
    try:
        import pymupdf
    except ImportError:
        return None
    with pymupdf.open(path) as doc:
        return " | ".join(line for page in doc for line in page.get_text().splitlines() if line.strip())


def printed(path):
    """The street line the PO prints as its job address, or None if code cannot read it."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".html", ".htm"):
        text = _cells(path.read_text(encoding="utf-8", errors="replace"))
    elif suffix == ".pdf":
        text = _pdf_text(path)
    else:
        return None
    found = JOB_ADDRESS.search(text + " |") if text else None
    return found.group(1).strip() if found else None


def plain(address):
    tokens = re.findall(r"[a-z0-9]+", address.lower())
    return " ".join(WORDS.get(t, t) for t in tokens)


def same(printed_line, typed):
    """True when the PO's street line is the address Sam typed (Drive and Dr count as one)."""
    po, sam = plain(printed_line), plain(typed)
    return bool(po) and (sam == po or sam.startswith(po + " "))
