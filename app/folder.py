"""The folder the runner drives: its stage paths and its own scripts. The runner never carries a copy
of the folder's rules; it loads the scripts from the folder it was started on."""
import importlib
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

    def houses(self):
        intake = self.stage("01 intake")
        return sorted(p.name for p in intake.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))


def highest(folder, stem, suffix=".md"):
    """The highest-numbered <stem>-N<suffix> in folder, or None."""
    best, best_n = None, 0
    for path in Path(folder).glob(f"{stem}-*{suffix}"):
        number = path.name[len(stem) + 1:-len(suffix)]
        if number.isdigit() and int(number) > best_n:
            best, best_n = path, int(number)
    return best
