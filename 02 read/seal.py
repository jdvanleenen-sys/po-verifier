"""Sam's yes, sealed. The only way a record becomes approved. Run from the folder root:

    python "02 read/seal.py" <file>

Use it on a read-back, review or outcome once Sam's plain yes, his name and the date are written
in its "Sam's yes" block. It refuses an answer that is not a yes, sets status: approved, and writes
a `sealed:` line: the file's name and a sha256 over that name and the text. Every reader of an
approved record checks the seal, so a record changed after Sam's yes, or copied under a new
number, is refused. Never set status: approved by hand, and never seal a file Sam did not answer.
"""
import hashlib
import re
import sys
from pathlib import Path

SEAL = re.compile(r"^sealed:\s*(\S+)\s+sha256\s+([0-9a-f]{64})\s*$", re.M)
SEAL_LINE = re.compile(r"^sealed:.*(?:\n|$)", re.M)
STATUS = re.compile(r"^status:\s*(\S*)\s*$", re.M)
ANSWER = re.compile(r"^-\s*Answer:[ \t]*(.*)$", re.M)
FILLED = {"Name": re.compile(r"^-\s*Name:[ \t]*\S", re.M), "Date": re.compile(r"^-\s*Date:[ \t]*\S", re.M)}
CHANGED = ("was changed after Sam's yes. Approved files never change: undo the edit; a correction is "
           "a new numbered file with its own yes")


def unsealed(text):
    """The text with any seal line taken out and line endings made plain."""
    return SEAL_LINE.sub("", text.replace("\r\n", "\n"))


def digest(name, text):
    return hashlib.sha256((name + "\n" + unsealed(text)).encode("utf-8")).hexdigest()


def is_approved(text):
    status = STATUS.search(text)
    return bool(status and status.group(1).lower() == "approved")


def yes_problems(text):
    """What is missing from Sam's yes. A yes is an Answer that starts with 'yes', with a name and date."""
    answer = ANSWER.search(text)
    said = answer.group(1).strip() if answer else ""
    problems = []
    if not re.match(r"yes\b", said, re.I):
        problems.append(f"has an Answer that is not a plain yes ('{said}'). Only an answer that starts "
                        "with yes counts; anything else leaves the stage open")
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


def main(argv):
    if len(argv) != 2:
        sys.exit('Use: python "02 read/seal.py" <file>')
    path = Path(argv[1])
    if not path.is_file():
        sys.exit(f"No file {path}.")
    try:
        sealed = seal_text(path.name, path.read_bytes().decode("utf-8-sig"))
    except ValueError as e:
        sys.exit(f"{path.name} was not sealed. It " + "; it ".join(e.args[0]) + ".")
    path.write_text(sealed, encoding="utf-8", newline="\n")
    print(f"{path.name} is approved and sealed. It must never change from here on.")


if __name__ == "__main__":
    main(sys.argv)
