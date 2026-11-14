"""Each step of one house, in order. Every step checks the files first, so a repeated tap or a
restart never does a step twice. Steps 3 to 6 are added as they are built."""
import json

import agent
import config
import houses


class Stopped(Exception):
    """A plain-words reason a step did not run."""


def _before_read(folder, house):
    path = folder.root / config.APP_DIR / house / "before-read.json"
    if not path.is_file():
        raise Stopped(f"{house} was not locked by the app, so its answers before the read are missing.")
    return json.loads(path.read_text(encoding="utf-8"))


def read_answers(before):
    """Sam's answers before the read, as lines for the read prompt."""
    measured = before["measured"]
    lines = [f"- Date measured: not recorded (Sam, {before['locked']})." if measured == "not recorded"
             else f"- Date measured: {measured} (Sam)."]
    for answer in before["answers"].values():
        lines.append(f"- {answer['ask']} Sam: \"Yes, these are the POs for {before['address']}.\" ({answer['date']})")
    return "\n".join(lines)


def start_read(folder, jobs, house):
    """Start the read for a locked house. Refused unless the house is on the Reading screen with no
    read-back yet; True if started, False if a read is already running."""
    state = houses.stand(folder, house, house in jobs.running())
    if state["screen"] != houses.READING:
        raise Stopped(f"{house} is past the read.")
    if state["busy"]:
        return False
    text = agent.prompt("read", house=house, answers=read_answers(_before_read(folder, house)))
    return jobs.start(house, "read", text)
