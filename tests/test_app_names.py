"""The runner loads the folder's own scripts by name next to its own modules, so no app module may
share a name with a stage script. A clash once made 33 of the folder's tests load the wrong module."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGES = ("00 setup", "01 intake", "02 read", "03 compare", "04 review", "05 request", "06 outcome")


class NoNameClash(unittest.TestCase):
    def test_no_app_module_shares_a_name_with_a_stage_script(self):
        app = {p.stem for p in (ROOT / "app").glob("*.py")}
        stage = {p.stem for s in STAGES if (ROOT / s).is_dir() for p in (ROOT / s).glob("*.py")}
        self.assertEqual(app & stage, set())


if __name__ == "__main__":
    unittest.main()
