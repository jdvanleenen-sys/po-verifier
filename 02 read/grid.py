"""The rule grid: every read-back row and every PO, checked against every rule, one cell each.

  python "02 read/grid.py" build <house> [--replace]
      Writes 02 read/<house>/grid-N.md for read-back-N.md (the highest N). Code fills every cell it
      can work out; the rest are "?". --replace rebuilds a grid whose read-back is still a draft.

  python "02 read/grid.py" check <house> [--final]
      Refuses the grid if any cell is blank or "?", a row or PO is missing or extra, a code cell
      was changed, any cell is "fail", an "at risk" row is not under At risk, or the read-back's
      tables changed after the grid was built. --final (03 compare and the money gate) also
      refuses "ask Sam". Without it, "ask Sam" cells pass and are counted.

The grid is how a skipped check stops being silent: the number of cells is fixed by code before
anyone checks anything, and a blank cell is a refusal.
"""
import re
import sys
from pathlib import Path

import prices
import seal
from grid_check import check_grid
from grid_read import render

ROOT = Path(__file__).resolve().parent.parent


def numbered(house, stem):
    folder = ROOT / "02 read" / house
    found = [(int(m.group(1)), p) for p in folder.glob(f"{stem}-*.md")
             if (m := re.match(rf"{stem}-(\d+)\.md$", p.name))]
    return max(found) if found else (None, None)


def grid_path_for(read_back_path):
    n = re.match(r"read-back-(\d+)\.md$", Path(read_back_path).name).group(1)
    return Path(read_back_path).with_name(f"grid-{n}.md")


def read(path):
    return Path(path).read_bytes().decode("utf-8-sig")


def build(house, replace=False):
    n, path = numbered(house, "read-back")
    if path is None:
        sys.exit(f"No read-back for {house} in 02 read/.")
    text, target = read(path), grid_path_for(path)
    if target.exists():
        if not replace:
            sys.exit(f"{target.name} exists. Use --replace only if {path.name} is still a draft.")
        if re.search(r"^status:\s*approved", text, re.M):
            sys.exit(f"{path.name} is approved, so its grid is never rebuilt. Write a new read-back.")
    snapshot = prices.snapshot_bytes(house, text)
    if snapshot is None:
        sys.exit("The read-back names no price list snapshot in its folder. Run prices.py snapshot first.")
    grid_text = render(house, n, text, snapshot)
    target.write_text(grid_text, encoding="utf-8")
    asks = len(re.findall(r"\| \?(?= \|)", grid_text))
    return f"{target.name} written: {asks} cell(s) are '?' for you to answer, one rule at a time."


def main(argv):
    if len(argv) < 3 or argv[1] not in ("build", "check"):
        sys.exit('Use: python "02 read/grid.py" build <house> [--replace] | check <house> [--final]')
    house, flags = argv[2], set(argv[3:])
    if argv[1] == "build":
        print(build(house, "--replace" in flags))
        return
    _, path = numbered(house, "read-back")
    if path is None:
        sys.exit(f"No read-back for {house} in 02 read/.")
    text, grid_file = read(path), grid_path_for(path)
    if not grid_file.exists():
        sys.exit(f"No {grid_file.name} for {path.name}. Run: python \"02 read/grid.py\" build {house}")
    problems, asks = check_grid(text, read(grid_file), prices.snapshot_bytes(house, text), "--final" in flags)
    if seal.is_approved(text):
        problems += [f"{path.name} {why}" for why in seal.approval_problems(text, path.name)]
    if problems:
        sys.exit(f"{grid_file.name} is refused:\n- " + "\n- ".join(problems))
    note = f" {asks} cell(s) wait on Sam; the house cannot leave 02 read until he answers." if asks else ""
    print(f"{grid_file.name}: every cell is filled and every code cell checks out.{note}")


if __name__ == "__main__":
    main(sys.argv)
