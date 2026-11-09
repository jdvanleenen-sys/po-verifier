"""The numbering of a house's records: each file's number, its attempt: line, the files below it, and
the one file its from: line names. Used by compare.py and the request script before they trust a
record."""
import re

NUMBERED = re.compile(r"(.+)-(\d+)\.md$")
ATTEMPT = re.compile(r"^attempt:[ \t]*(.*)$", re.M)
FROM = re.compile(r"^from:[ \t]*(.*)$", re.M)


def chain_problems(path, text, root):
    """Every numbering problem with one record. root is the folder the from: line is read against."""
    found = NUMBERED.match(path.name)
    if not found:
        return []
    stem, n = found.group(1), int(found.group(2))
    problems = []
    attempt = ATTEMPT.search(text)
    if attempt and attempt.group(1).strip() != str(n):
        problems.append(f"{path.name} says attempt: {attempt.group(1).strip()}, but its file name says {n}. "
                        "The two must agree")
    gaps = [f"{stem}-{k}.md" for k in range(1, n) if not path.with_name(f"{stem}-{k}.md").exists()]
    if gaps:
        problems.append(f"{path.name} leaves a gap: {', '.join(gaps)} is missing below it. Files are "
                        "numbered 1, 2, 3 with no gap, and none is ever deleted or renamed")
    origin = FROM.search(text)
    if origin is not None:
        named = origin.group(1).strip().strip("`").strip()
        if not named or not (root / named).exists():
            problems.append(f"{path.name}: from: must name exactly one file or folder that exists, such as "
                            f"02 read/<house>/read-back-1.md; it says '{origin.group(1).strip()}'")
    return problems
