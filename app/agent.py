"""The headless agent: one task, run in the folder, with a time limit. This is the only place the
runner talks to a model, so approach B (the Claude API) would replace this file and nothing else."""
import json
import subprocess
import time
from pathlib import Path

import config

PROMPTS = Path(__file__).resolve().parent / "prompts"


def prompt(name, **fields):
    text = (PROMPTS / f"{name}.md").read_text(encoding="utf-8")
    for key, value in fields.items():
        text = text.replace("{" + key + "}", value)
    return text


def _outcome(returncode, out, err, seconds):
    try:
        result = json.loads(out)
    except ValueError:
        return {"ok": False, "line": (err or out or "The reader gave no answer.").strip()[-400:],
                "seconds": seconds, "cost": None}
    lines = (result.get("result") or "").strip().splitlines()
    line = lines[-1].strip() if lines else ""
    ok = returncode == 0 and not result.get("is_error") and line.startswith("DONE")
    return {"ok": ok, "line": line or "The reader gave no answer.", "seconds": seconds,
            "cost": result.get("total_cost_usd")}


def run(folder, text, limit, keep):
    """Run the agent in the folder's top level with text on stdin and wait up to limit seconds.
    keep(process) is called once it starts, so a Stop tap can end it. Returns {"ok", "line",
    "seconds", "cost"}; "line" is the agent's last line."""
    started = time.monotonic()
    proc = subprocess.Popen(config.AGENT_COMMAND, cwd=folder.root, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    keep(proc)
    try:
        out, err = proc.communicate(text, timeout=limit)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return {"ok": False, "line": f"Stopped: the read ran past {limit // 60} minutes.",
                "seconds": round(time.monotonic() - started), "cost": None}
    return _outcome(proc.returncode, out, err, round(time.monotonic() - started))
