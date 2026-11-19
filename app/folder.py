"""The folder the runner drives: its stage paths and its own scripts. The runner never carries a copy
of the folder's rules; it loads the scripts from the folder it was started on."""
import importlib
import json
import sys
from pathlib import Path

STAGES = ("01 intake", "02 read", "03 compare", "04 review", "05 request", "06 outcome")


class Folder:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not (self.root / "reference" / "contractor.md").is_file():
            raise SystemExit(f"{self.root} has no reference/contractor.md, so it is not a set-up folder.")

    def stage(self, name, house=None):
        path = self.root / name
        return path / house if house else path

    def script(self, stage, module):
        """A module from one of the folder's stage folders, such as script("02 read", "seal")."""
        where = str(self.stage(stage))
        if where not in sys.path:
            sys.path.insert(0, where)
        return importlib.import_module(module)

    def practice(self):
        """True for the practice folder (its contractor.md says "practice stand-ins")."""
        # The same test as "practice" in 02 read/contractor.py read(); read here directly so the
        # house list never depends on importing a stage script.
        text = (self.root / "reference" / "contractor.md").read_text(encoding="utf-8-sig")
        return "practice stand-in" in text.lower()

    def hidden(self):
        """Houses kept out of the app, listed in _app/hidden.json ({"houses": [...], "why": "..."}).
        Their records stay where they are; delete the file to show them again."""
        path = self.root / "_app" / "hidden.json"
        if not path.is_file():
            return set()
        return set(json.loads(path.read_text(encoding="utf-8")).get("houses", []))

    def houses(self):
        """Every house folder in intake. In a real contractor's folder, only his houses (real-N):
        the practice houses that ship with the folder are not his and never show on his phone.
        Hidden houses never show and never block a new upload."""
        intake = self.stage("01 intake")
        found = sorted(p.name for p in intake.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
        found = [h for h in found if h not in self.hidden()]
        return found if self.practice() else [h for h in found if h.startswith("real-")]


def highest(folder, stem, suffix=".md"):
    """The highest-numbered <stem>-N<suffix> in folder, or None."""
    best, best_n = None, 0
    for path in Path(folder).glob(f"{stem}-*{suffix}"):
        number = path.name[len(stem) + 1:-len(suffix)]
        if number.isdigit() and int(number) > best_n:
            best, best_n = path, int(number)
    return best
