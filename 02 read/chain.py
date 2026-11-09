"""The numbering of a house's records: each file's number, its attempt: line, the files below it, and
the one file its from: line names. Used by compare.py and the request script before they trust a
record."""
import re

NUMBERED = re.compile(r"(.+)-(\d+)\.md$")
ATTEMPT = re.compile(r"^attempt:[ \t]*(.*)$", re.M)
FROM = re.compile(r"^from:[ \t]*(.*)$", re.M)


def gap_problems(path):
    """The numbered files missing below this one, as a refusal; [] when there is no gap."""
    found = NUMBERED.match(path.name)
    if not found:
        return []
    stem, n = found.group(1), int(found.group(2))
    gaps = [f"{stem}-{k}.md" for k in range(1, n) if not path.with_name(f"{stem}-{k}.md").exists()]
    if not gaps:
        return []
    return [f"{path.name} leaves a gap: {', '.join(gaps)} is missing below it. Files are "
            "numbered 1, 2, 3 with no gap, and none is ever deleted or renamed"]


def chain_problems(path, text, root):
    """Every numbering problem with one record. root is the folder the from: line is read against."""
    found = NUMBERED.match(path.name)
    if not found:
        return []
    n = int(found.group(2))
    problems = []
    attempt = ATTEMPT.search(text)
    if attempt is None:
        problems.append(f"{path.name} has no attempt: line. Every numbered record carries attempt: N, the "
                        "same N as its file name")
    elif attempt.group(1).strip() != str(n):
        problems.append(f"{path.name} says attempt: {attempt.group(1).strip()}, but its file name says {n}. "
                        "The two must agree")
    problems += gap_problems(path)
    origin = FROM.search(text)
    if origin is None:
        problems.append(f"{path.name} has no from: line. Every numbered record names the one file or folder "
                        "it was made from, such as from: 02 read/<house>/read-back-1.md")
    else:
        named = origin.group(1).strip().strip("`").strip()
        if not named or not (root / named).exists():
            problems.append(f"{path.name}: from: must name exactly one file or folder that exists, such as "
                            f"02 read/<house>/read-back-1.md; it says '{origin.group(1).strip()}'")
        elif not same_house(named, path):
            problems.append(f"{path.name}: from: names '{named}', which is not this house's "
                            f"({path.parent.name}) own record. A record comes only from its own house, "
                            "in its own stage or the stage before")
    return problems


STAGES = ("01 intake", "02 read", "03 compare", "04 review", "05 request", "06 outcome")


def same_house(named, path):
    """The from: path is in this house's folder, in this record's stage or an earlier one."""
    parts = named.replace("\\", "/").strip("/").split("/")
    stage, house = path.parent.parent.name, path.parent.name
    if len(parts) < 2 or parts[1] != house or parts[0] not in STAGES or stage not in STAGES:
        return False
    return STAGES.index(parts[0]) <= STAGES.index(stage)
