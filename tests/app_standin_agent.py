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
import sys
import time
from pathlib import Path


def main():
    text = sys.stdin.read()
    if os.environ.get("STANDIN_PROMPT_OUT"):
        Path(os.environ["STANDIN_PROMPT_OUT"]).write_text(text, encoding="utf-8")
    mode = os.environ.get("STANDIN_MODE", "draft")
    house = re.search(r"for the house (\S+)\.", text).group(1)
    if mode == "slow":
        time.sleep(60)
    if mode == "garbage":
        print("not json")
        return
    if mode == "stopped":
        print(json.dumps({"result": "STOPPED: a stand-in reason", "is_error": False, "total_cost_usd": 0}))
        return
    out = Path("02 read") / house
    out.mkdir(parents=True, exist_ok=True)
    (out / "read-back-1.md").write_text(f"---\nhouse: {house}\nattempt: 1\nstage: 02 read\n"
                                        f"from: 01 intake/{house}/\nstatus: draft\n---\n", encoding="utf-8")
    print(json.dumps({"result": f"working\nDONE {house} read-back-1, 0 questions for Sam",
                      "is_error": False, "total_cost_usd": 0}))


if __name__ == "__main__":
    main()
