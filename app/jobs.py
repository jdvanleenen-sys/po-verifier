"""One agent job per house at a time, run in the background. Each job's state is written to the
runner's own folder as it changes, so a restart knows a job was cut short instead of guessing."""
import json
import threading
import time
from datetime import datetime

import agent
import config


class Jobs:
    def __init__(self, folder):
        self.folder = folder
        self._guard = threading.Lock()
        self._live = {}

    def _record(self, house):
        return self.folder.root / config.APP_DIR / house / "job.json"

    def _write(self, house, state):
        path = self._record(house)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=1), encoding="utf-8")

    def running(self):
        with self._guard:
            return set(self._live)

    def status(self, house):
        """The last job's state. A job the file says is running but this runner is not running was
        cut short (the laptop restarted): it shows as interrupted."""
        path = self._record(house)
        if not path.is_file():
            return None
        state = json.loads(path.read_text(encoding="utf-8"))
        with self._guard:
            live = self._live.get(house)
        if state.get("status") == "running":
            if live is None:
                state["status"] = "interrupted"
            else:
                state["elapsed"] = round(time.monotonic() - live["t0"])
                state["long"] = state["elapsed"] > config.READ_WARN_SECONDS
        return state

    def start(self, house, kind, text):
        """Start a job; False if one is already running for this house (a second tap does nothing)."""
        with self._guard:
            if house in self._live:
                return False
            self._live[house] = {"proc": None, "t0": time.monotonic(), "stopped": False}
        self._write(house, {"kind": kind, "status": "running", "started": datetime.now().isoformat(timespec="seconds")})
        threading.Thread(target=self._run, args=(house, kind, text), daemon=True).start()
        return True

    def _keep(self, house):
        def keep(proc):
            with self._guard:
                self._live[house]["proc"] = proc
                stopped_early = self._live[house]["stopped"]
            if stopped_early:
                proc.kill()
        return keep

    def _run(self, house, kind, text):
        try:
            outcome = agent.run(self.folder, text, config.READ_LIMIT_SECONDS, self._keep(house))
        except OSError as err:
            outcome = {"ok": False, "line": f"The reader could not start: {err}", "seconds": 0, "cost": None}
        with self._guard:
            live = self._live.pop(house, {})
        if live.get("stopped"):
            outcome = {**outcome, "ok": False, "line": "Stopped by Sam."}
        status = "done" if outcome["ok"] else ("stopped" if live.get("stopped") else "failed")
        self._write(house, {"kind": kind, "status": status, **outcome})

    def stop(self, house):
        with self._guard:
            live = self._live.get(house)
            if not live:
                return False
            live["stopped"] = True
            proc = live["proc"]
        if proc is not None:
            proc.kill()
        return True

    def wait(self, house, seconds=30):
        """For tests and the command line: wait until this house has no running job."""
        end = time.monotonic() + seconds
        while house in self.running() and time.monotonic() < end:
            time.sleep(0.05)
        return house not in self.running()
