"""A stand-in for the headless agent in the phone app's tests. It calls no model. It reads the prompt
on stdin, saves it where STANDIN_PROMPT_OUT says, and acts by STANDIN_MODE:

    draft    write a draft 02 read/<house>/read-back-1.md and answer DONE (the default)
    stopped  write nothing and answer STOPPED with a reason
    slow     wait 60 seconds first (for Stop and the time limit)
    garbage  print something that is not the agent's JSON
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def main():
    text = sys.stdin.read()
    if os.environ.get("STANDIN_PROMPT_OUT"):
        Path(os.environ["STANDIN_PROMPT_OUT"]).write_text(text, encoding="utf-8")
    mode = os.environ.get("STANDIN_MODE", "draft")
    house = re.search(r"\bhouse ([a-z0-9-]+)", text).group(1)
    nxt = re.search(r"next numbered read-back, `02 read/[^/`]+/(read-back-\d+)\.md`", text)
    name = nxt.group(1) if nxt else "read-back-1"
    if mode == "slow":
        time.sleep(60)
    if mode == "garbage":
        print("not json")
        return
    if mode == "stopped":
        print(json.dumps({"result": "STOPPED: a stand-in reason", "is_error": False, "total_cost_usd": 0}))
        return
    if "is in stage 05 request" in text:
        notes = re.search(r"--notes (\S+?)`", text).group(1)
        done = subprocess.run([sys.executable, "05 request/build_request.py", "build", house, "--notes", notes],
                              capture_output=True, text=True)
        line = f"DONE {house} request built, six checks pass" if done.returncode == 0 else "STOPPED: build failed"
        print(json.dumps({"result": line, "is_error": False, "total_cost_usd": 0}))
        return
    out = Path("02 read") / house
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.md").write_text(f"---\nhouse: {house}\nattempt: {name[10:]}\nstage: 02 read\n"
                                    f"from: 01 intake/{house}/\nstatus: draft\n---\n", encoding="utf-8")
    print(json.dumps({"result": f"working\nDONE {house} {name}, 0 questions for Sam",
                      "is_error": False, "total_cost_usd": 0}))


if __name__ == "__main__":
    main()
