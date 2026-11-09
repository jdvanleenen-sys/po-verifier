"""Sam's yes, sealed. The only way a record becomes approved. Run from the folder root:

    python "02 read/seal.py" <file>

Use it on a read-back, review or outcome once Sam's plain yes, his name and the date are written
in its "Sam's yes" block. It refuses an answer that is not a yes, sets status: approved, and writes
a `sealed:` line: the file's name and a sha256 over that name and the text. It also writes one
line in the folder's ledger, `seals.md`: the file, its seal, and for a read-back the sha256 of its
grid. A file is sealed once: a name already in the ledger is refused, so an approved file edited
and sealed again is caught. Every reader of an approved record on disk checks the seal and the
ledger, so a record changed after Sam's yes, copied under a new number, or whose grid changed, is
refused. Never set status: approved by hand, and never seal a file Sam did not answer.
"""
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

LEDGER = "seals.md"
LEDGER_HEAD = ("# Seals\n\nWritten by 02 read/seal.py, one line per approved record. Never edit this file.\n\n"
               "| File | Seal sha256 | Grid sha256 | Sealed on |\n|---|---|---|---|\n")
LEDGER_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([0-9a-f]{64})\s*\|\s*([0-9a-f]{64}|none)\s*\|", re.M)

SEAL = re.compile(r"^sealed:\s*(\S+)\s+sha256\s+([0-9a-f]{64})\s*$", re.M)
SEAL_LINE = re.compile(r"^sealed:.*(?:\n|$)", re.M)
STATUS = re.compile(r"^status:\s*(\S*)\s*$", re.M)
ANSWER = re.compile(r"^-\s*Answer:[ \t]*(.*)$", re.M)
FILLED = {"Name": re.compile(r"^-\s*Name:[ \t]*\S", re.M), "Date": re.compile(r"^-\s*Date:[ \t]*\S", re.M)}
CHANGED = ("was changed after Sam's yes. Approved files never change: undo the edit; a correction is "
           "a new numbered file with its own yes")


def read_record(path):
    """A record's text, written by any editor as UTF-8 (with or without a BOM) or UTF-16. Anything
    else stops in plain words, never a traceback."""
    raw = Path(path).read_bytes()
    try:
        if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
            return raw.decode("utf-16")
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise SystemExit(f"{Path(path).name} is not saved as UTF-8. Save it as UTF-8 and run again.")


def unsealed(text):
    """The text with any seal line taken out and line endings made plain."""
    return SEAL_LINE.sub("", text.replace("\r\n", "\n"))


def digest(name, text):
    return hashlib.sha256((name + "\n" + unsealed(text)).encode("utf-8")).hexdigest()


def is_approved(text):
    status = STATUS.search(text)
    return bool(status and status.group(1).lower() == "approved")


PLAIN_YES = re.compile(r"yes(?:,?\s+to the (?:whole table|table exactly as shown|table with those decisions))?\.?",
                       re.I)


def yes_problems(text):
    """What is missing from Sam's yes. A yes is the Answer 'yes' alone or one of the three plain forms
    ('yes, to the whole table', '... exactly as shown', '... with those decisions'), with a name and
    date. A condition or a question after the yes ('Yes, but...', 'Yes?') is not a yes."""
    answer = ANSWER.search(text)
    said = answer.group(1).strip() if answer else ""
    problems = []
    if not PLAIN_YES.fullmatch(said):
        problems.append(f"has an Answer that is not a plain yes: '{said}'. A condition or a question means "
                        "the table changes first")
    problems += [f"has no {k} under Sam's yes" for k, pattern in FILLED.items() if not pattern.search(text)]
    return problems


def seal_problems(text, name=None):
    """Problems with the seal of a record marked approved. name: the file name it is read under."""
    found = SEAL.search(text)
    if not found:
        return ["is marked approved but has no seal. Only seal.py marks a record approved, after Sam's "
                "yes is written: python \"02 read/seal.py\" <file>"]
    if name and found.group(1) != name:
        return [f"carries the seal of {found.group(1)}: an approved file copied under a new name. A "
                "correction is a new numbered file with its own yes"]
    return [] if digest(found.group(1), text) == found.group(2) else [CHANGED]


def approval_problems(text, name=None):
    """Every reason a record does not count as approved. Each reads after the record's name."""
    if not is_approved(text):
        return ["does not carry Sam's approval (status: approved and his yes)"]
    return yes_problems(text) + seal_problems(text, name)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_beside(path):
    """The grid that goes with a read-back (read-back-N.md has grid-N.md beside it), or None."""
    path = Path(path)
    if not path.name.startswith("read-back-"):
        return None
    grid = path.with_name(path.name.replace("read-back-", "grid-", 1))
    return grid if grid.is_file() else None


def ledger(folder):
    """{file name: (seal sha256, grid sha256 or None)} from the folder's seals.md."""
    book = Path(folder) / LEDGER
    text = book.read_text(encoding="utf-8-sig") if book.is_file() else ""
    return {m.group(1): (m.group(2), None if m.group(3) == "none" else m.group(3))
            for m in LEDGER_ROW.finditer(text)}


def ledger_problems(path, text):
    """For an approved record on disk: its seal is the one in the ledger, and its grid is unchanged."""
    path = Path(path)
    if not is_approved(text):
        return []
    entry = ledger(path.parent).get(path.name)
    if entry is None:
        return [f"is approved but is in no line of {LEDGER}, so it was not sealed by seal.py after Sam's "
                "yes. A correction is a new numbered file with its own yes"]
    found = SEAL.search(text)
    if not found or found.group(2) != entry[0]:
        return [CHANGED]
    grid = grid_beside(path)
    if entry[1] and (grid is None or sha256_file(grid) != entry[1]):
        return [f"has its grid {path.name.replace('read-back-', 'grid-', 1)} changed after Sam's yes on "
                f"{path.name}. The grid never changes after the yes: put it back, or write the next read-back"]
    return []


def file_approval_problems(path, text=None):
    """Every reason a record on disk does not count as approved: its seal, then the ledger."""
    path = Path(path)
    text = read_record(path) if text is None else text
    return approval_problems(text, path.name) or ledger_problems(path, text)


def seal_text(name, text):
    """The record approved and sealed under this file name. Raises ValueError with the reasons not to."""
    problems = yes_problems(text)
    if SEAL.search(text):
        problems.append("is already sealed. A sealed record never changes; a correction is a new "
                        "numbered file")
    if not STATUS.search(text):
        problems.append("has no status: line in its front matter")
    if problems:
        raise ValueError(problems)
    text = STATUS.sub("status: approved", text.replace("\r\n", "\n"), count=1)
    line = f"sealed: {name} sha256 {digest(name, text)}"
    return STATUS.sub(lambda m: m.group(0) + "\n" + line, text, count=1)


USED_BY = re.compile(r"^from(?: review)?:[ \t]*`?([^`\n]+?)`?[ \t]*$", re.M)


def used_by(path):
    """Other records of this house that already name this record in a from: or 'from review:' line."""
    path = Path(path).resolve()
    root, house, stage = path.parent.parent.parent, path.parent.name, path.parent.parent.name
    own = f"{stage}/{house}/{path.name}".lower()
    own_grid = path.with_name(path.name.replace("read-back-", "grid-", 1)).resolve()  # built before the yes
    users = []
    for other in sorted(root.glob(f"*/{house}/*.md")):
        if other.resolve() == path or other.name == LEDGER or other.resolve() == own_grid:
            continue
        try:
            text = read_record(other)
        except SystemExit:
            continue
        if any(m.group(1).strip().replace("\\", "/").lower() == own for m in USED_BY.finditer(text)):
            users.append(other.name)
    return users


def seal_file(path, today=None):
    """Seal the record at path and write its ledger line. Raises ValueError with the reasons not to."""
    path = Path(path)
    users = used_by(path)
    if users:
        raise ValueError([f"is already used by {', '.join(users)}: a record another file was built from is "
                          "never approved after the fact. Write the next number"])
    if path.name in ledger(path.parent):
        raise ValueError([f"was sealed before (it is in {LEDGER}). An approved file is never re-approved: "
                          "write the next number"])
    sealed = seal_text(path.name, read_record(path))
    grid = grid_beside(path)
    path.write_text(sealed, encoding="utf-8", newline="\n")
    book = path.parent / LEDGER
    row = (f"| {path.name} | {SEAL.search(sealed).group(2)} | {sha256_file(grid) if grid else 'none'} | "
           f"{today or date.today().isoformat()} |\n")
    head = "" if book.is_file() and book.stat().st_size else LEDGER_HEAD
    with open(book, "a", encoding="utf-8", newline="\n") as f:
        f.write(head + row)
    return sealed


def main(argv):
    if len(argv) != 2:
        sys.exit('Use: python "02 read/seal.py" <file>')
    path = Path(argv[1])
    if not path.is_file():
        sys.exit(f"No file {path}.")
    try:
        seal_file(path)
    except ValueError as e:
        sys.exit(f"{path.name} was not sealed. It " + "; it ".join(e.args[0]) + ".")
    print(f"{path.name} is approved and sealed. It must never change from here on.")


if __name__ == "__main__":
    main(sys.argv)
