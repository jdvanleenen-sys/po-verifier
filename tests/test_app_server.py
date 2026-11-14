"""The phone app's web server, driven like the phone drives it: the key, the house list, a new house
from upload to the Check screen, the plain-words errors, and 77 Mockup Drive from its sealed
read-back to an approved request through the routes. The agent is a stand-in."""
import io
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

try:
    import server  # noqa: E402
except ImportError:  # Flask not installed: the runner's own tests still run
    server = None
import config  # noqa: E402
from folder import Folder  # noqa: E402

LEAVE_OUT = shutil.ignore_patterns(".git", ".venv", "tests", "docs", "_for-testers", "__pycache__", "real-*", "app")
STANDIN = [sys.executable, str(ROOT / "tests" / "app_standin_agent.py")]
KEY = "test-key"


@unittest.skipIf(server is None, "needs Flask (pip install -r app/requirements.txt)")
class Server(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT, self.tmp / "f", ignore=LEAVE_OUT)
        self.folder = Folder(self.tmp / "f")
        patcher = mock.patch.object(config, "AGENT_COMMAND", STANDIN)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = server.create_app(self.folder, KEY).test_client()
        self.assertEqual(self.client.get(f"/?k={KEY}").status_code, 200)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def wait(self, house, seconds=120):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            data = self.client.get(f"/api/house/{house}").get_json()
            if not data["busy"]:
                return data
            time.sleep(0.2)
        self.fail("still busy")

    def test_without_the_key_nothing_answers(self):
        bare = server.create_app(self.folder, KEY).test_client()
        for path in ("/", "/api/houses", "/api/house/77-mockup-drive"):
            self.assertEqual(bare.get(path).status_code, 403)
        self.assertEqual(bare.get("/api/houses?k=wrong").status_code, 403)

    def test_house_list_and_unknown_house(self):
        names = [h["house"] for h in self.client.get("/api/houses").get_json()]
        self.assertIn("77-mockup-drive", names)
        self.assertEqual(self.client.get("/api/house/no-such").status_code, 404)
        self.assertEqual(self.client.get("/api/house/..%2F..%2Fetc").status_code, 404)

    def test_new_house_from_upload_to_the_check_screen(self):
        shutil.rmtree(self.folder.stage("01 intake", "77-mockup-drive"))
        sample = ROOT / "01 intake" / "77-mockup-drive"
        pos = [(io.BytesIO(p.read_bytes()), p.name) for p in sorted(sample.glob("PO *.html"))]
        held = self.client.post("/api/hold", data={"address": "77 Mockup Drive", "measured": "2026-11-12",
                                                   "covers": "no", "pos": pos,
                                                   "notes": [(io.BytesIO(b"8' doors 12"), "site-notes.txt")]},
                                content_type="multipart/form-data").get_json()
        self.assertEqual(held["questions"], [])
        house = self.client.post("/api/lock", json={"id": held["id"], "answers": {}}).get_json()["house"]
        self.assertEqual(self.wait(house)["screen"], "check")

    def test_refusal_comes_back_in_plain_words(self):
        answer = self.client.post("/api/hold", data={"address": ""}, content_type="multipart/form-data")
        self.assertEqual(answer.status_code, 400)
        self.assertEqual(answer.get_json()["error"], "Type the house address.")
        self.assertEqual(self.client.post("/api/house/77-mockup-drive/dance", json={}).status_code, 400)

    def test_whole_house_through_the_routes(self):
        for stage in ("03 compare", "04 review", "05 request"):
            shutil.rmtree(self.folder.stage(stage, "77-mockup-drive"))
        with mock.patch("steps.date") as fake:
            fake.today.return_value = __import__("datetime").date(2026, 10, 17)
            shown = self.client.get("/api/house/77-mockup-drive").get_json()
            self.assertEqual(shown["screen"], "difference")
            picks = {"7": {"on": True, "epo": ""}}
            self.assertEqual(self.client.post("/api/house/77-mockup-drive/review",
                                              json={"picks": picks, "notes": "yes"}).status_code, 200)
            shown = self.wait("77-mockup-drive")
            self.assertEqual((shown["screen"], shown["passed"]), ("pdf", True))
            self.assertEqual(self.client.get("/api/house/77-mockup-drive/pdf").status_code, 200)
            approved = self.client.post("/api/house/77-mockup-drive/approve", json={}).get_json()
        self.assertEqual(approved["pdf"], "vpo-request-1.pdf")
        done = self.client.get("/api/house/77-mockup-drive").get_json()
        self.assertEqual((done["screen"], done["document"], done["sent"]), ("done", "VR-0001", False))
        self.client.post("/api/house/77-mockup-drive/sent", json={})
        self.assertTrue(self.client.get("/api/house/77-mockup-drive").get_json()["sent"])
        self.assertEqual(self.client.get("/api/house/77-mockup-drive/pdf?numbered=1").status_code, 200)


if __name__ == "__main__":
    unittest.main()
