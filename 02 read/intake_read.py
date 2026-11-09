"""The intake files a read-back was read from, fingerprinted in its rule grid.

grid.py build writes an "Intake read" table (each file under 01 intake/<house>/ and its sha256)
into the grid. Before a request is built or numbered, every file must still be there, unchanged,
and nothing may have been added: a changed PO would make the request disagree with its own proof,
and a file dropped in later was never read. Intake also never changes across read-backs: every later
grid is checked against the house's first grid, so an edit made before a new read-back is not
fingerprinted afresh and forgotten.
"""
import hashlib
import re
from pathlib import Path

HEADING = "## Intake read"
GRID = re.compile(r"^grid-(\d+)\.md$")
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([0-9a-f]{64})\s*\|\s*$")


def fingerprints(folder):
    """{path relative to the house's intake folder: sha256} for every file in it."""
    folder = Path(folder)
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def section(folder):
    lines = [HEADING, "Every file in `01 intake` when this grid was built. Written by `grid.py`; "
             "never edit it. A request is refused if any of these changes.", "",
             "| File | sha256 |", "|---|---|"]
    lines += [f"| `{name}` | {digest} |" for name, digest in fingerprints(folder).items()]
    return lines + [""]


def recorded(grid_text):
    """The fingerprints a grid recorded, or None if it has no Intake read table."""
    if HEADING not in (grid_text or ""):
        return None
    body = grid_text.split(HEADING, 1)[1].split("\n## ", 1)[0]
    return {m.group(1): m.group(2) for line in body.splitlines() if (m := ROW.match(line.strip()))}


def problems(folder, grid_text, house):
    """Every intake file changed, added or removed since the grid was built."""
    then = recorded(grid_text)
    if then is None:
        return [f"the rule grid has no Intake read table, so nothing shows what 01 intake/{house}/ held "
                "when it was read. Write a new read-back and build its grid with grid.py"]
    now = fingerprints(folder)
    found = [f"01 intake/{house}/{n} changed after it was read. Intake never changes: put the original back"
             for n in sorted(set(now) & set(then)) if now[n] != then[n]]
    found += [f"01 intake/{house}/{n} was added after the read. A new file means a new read-back "
              "(check it is for this house first)" for n in sorted(set(now) - set(then))]
    found += [f"01 intake/{house}/{n} was read but is gone. Intake never changes: put it back"
              for n in sorted(set(then) - set(now))]
    return found


def first_read(read_folder, below=None):
    """(grid name, fingerprints) of the house's first grid with an Intake read table, among the grids
    numbered below `below` (all of them when None). None when there is no such grid."""
    grids = sorted((int(m.group(1)), p) for p in Path(read_folder).glob("grid-*.md") if (m := GRID.match(p.name)))
    for n, path in grids:
        if below is not None and n >= below:
            break
        then = recorded(path.read_text(encoding="utf-8-sig", errors="replace"))
        if then is not None:
            return path.name, then
    return None


def latest_number(read_folder):
    """The highest grid number in the house's 02 read folder, or None."""
    found = [int(m.group(1)) for p in Path(read_folder).glob("grid-*.md") if (m := GRID.match(p.name))]
    return max(found) if found else None


def since_first_problems(folder, read_folder, house, below=None):
    """Every intake file changed, added or removed since the house's first read."""
    first = first_read(read_folder, below)
    if first is None:
        return []
    name, then = first
    now = fingerprints(folder)
    found = [f"01 intake/{house}/{n} changed after the first read ({name}): put the original back"
             for n in sorted(set(now) & set(then)) if now[n] != then[n]]
    found += [f"01 intake/{house}/{n} was added after the first read ({name}). Intake never changes once a "
              "house is read: take it out, and ask Sam how to handle a new document for this house"
              for n in sorted(set(now) - set(then))]
    found += [f"01 intake/{house}/{n} was read in {name} but is gone: put it back"
              for n in sorted(set(then) - set(now))]
    return found
