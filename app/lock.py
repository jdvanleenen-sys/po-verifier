"""New house: hold the uploads, ask what must be asked before the read, then lock them into intake.

Two steps, so nothing reaches 01 intake until Sam has answered: hold() keeps the files in the
runner's own folder and lists the questions; lock() writes intake once, with house-info.md built from
his answers by code. After lock() nothing writes to that intake folder again."""
import json
import re
import secrets
import shutil
from datetime import date
from pathlib import Path

import config
import po_address

SAFE = re.compile(r"[^A-Za-z0-9 ._,()-]")
NOT_RECORDED = "not recorded"


class Refused(Exception):
    """A plain-words reason the upload or answer was not taken."""


def _clean_name(name, fallback, taken):
    stem_ext = SAFE.sub("_", Path(name or "").name).strip(" .")
    stem, ext = Path(stem_ext).stem or fallback, Path(stem_ext).suffix.lower()
    candidate, n = f"{stem}{ext}", 2
    while candidate.lower() in taken:
        candidate, n = f"{stem}-{n}{ext}", n + 1
    taken.add(candidate.lower())
    return candidate


def _check_files(files, allowed, what):
    if not files:
        raise Refused(f"Add at least one {what}.")
    for name, data in files:
        if Path(name or "").suffix.lower() not in allowed:
            raise Refused(f"{name} is not a file the folder can read. Use {', '.join(allowed)}.")
        if not data:
            raise Refused(f"{name} is empty. Add it again.")
        if len(data) > config.MAX_FILE_BYTES:
            raise Refused(f"{name} is over {config.MAX_FILE_BYTES // (1024 * 1024)} MB.")


def _measured(value):
    value = (value or "").strip().lower()
    if value == NOT_RECORDED:
        return NOT_RECORDED
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise Refused("Give the date measured, or say it was not recorded.")


def hold(folder, address, measured, covers_others, pos, notes):
    """Keep the uploads aside and return {"id", "questions"}. Raises Refused in plain words."""
    address = " ".join((address or "").split())
    if not address:
        raise Refused("Type the house address.")
    _check_files(pos, config.PO_TYPES, "PO")
    _check_files(notes, config.NOTES_TYPES, "notes photo or file")
    held_id = secrets.token_hex(8)
    where = folder.root / config.APP_DIR / "held" / held_id
    where.mkdir(parents=True)
    taken, saved = set(), {"pos": [], "notes": []}
    for kind, files, fallback in (("pos", pos, "po"), ("notes", notes, "site-notes")):
        for name, data in files:
            clean = _clean_name(name, fallback, taken)
            (where / clean).write_bytes(data)
            saved[kind].append(clean)
    info = {"address": address, "measured": _measured(measured), "covers_others": bool(covers_others), **saved}
    info["questions"] = _questions(where, info)
    (where / "held.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    return {"id": held_id, "questions": info["questions"]}


def _questions(where, info):
    """Questions the read cannot settle without Sam. Today: a PO printing another job address."""
    printed = {name: po_address.printed(where / name) for name in info["pos"]}
    odd = sorted({line for line in printed.values() if line and not po_address.same(line, info["address"])})
    if not odd:
        return []
    shown = " and ".join(f'"{line}"' for line in odd)
    return [{"id": "address", "ask": f"These POs print the job address {shown}. Are they the POs for "
             f"{info['address']}?", "printed": odd}]


def _next_house(folder):
    used = {p.name for stage in ("01 intake", "02 read", "03 compare", "04 review", "05 request")
            for p in folder.stage(stage).glob("real-*")}
    n = 1
    while f"real-{n}" in used:
        n += 1
    return f"real-{n}"


def _house_info(info, today):
    measured = "" if info["measured"] == NOT_RECORDED else info["measured"]
    lines = ["# House info", "", "Real house. Private. Written by the PO Checker app from Sam's answers on the "
             "New house screen.", "", f"- Address: {info['address']}", "- Lot:", "- Builder:",
             f"- Date measured: {measured}", f"- Date dropped in: {today}", ""]
    if info["covers_others"]:
        lines += ["The notes page covers other houses too. It covers two houses or more; only the part "
                  f"for {info['address']} is this house.", ""]
    return "\n".join(lines)


def lock(folder, held_id, answers, today=None):
    """Write the held files into a new 01 intake/real-N/ and return the house name. answers holds
    {"address": "yes" | "no"} when that question was asked."""
    if not re.fullmatch(r"[0-9a-f]{16}", held_id or ""):
        raise Refused("That upload is not known. Start the house again.")
    where = folder.root / config.APP_DIR / "held" / held_id
    if not (where / "held.json").is_file():
        raise Refused("That upload is not known, or is already locked. Start the house again.")
    info = json.loads((where / "held.json").read_text(encoding="utf-8"))
    today = (today or date.today()).isoformat()
    said = {}
    for question in info["questions"]:
        reply = (answers or {}).get(question["id"], "").strip().lower()
        if reply not in ("yes", "no"):
            raise Refused(question["ask"])
        if reply == "no":
            raise Refused("Then these POs are for another house. Start again with this house's POs.")
        said[question["id"]] = {"ask": question["ask"], "answer": "yes", "date": today}
    house = _next_house(folder)
    intake = folder.stage("01 intake", house)
    intake.mkdir(parents=True)
    for name in info["pos"] + info["notes"]:
        shutil.copy2(where / name, intake / name)
    (intake / "house-info.md").write_text(_house_info(info, today), encoding="utf-8")
    record = folder.root / config.APP_DIR / house
    record.mkdir(parents=True, exist_ok=True)
    before = {"address": info["address"], "measured": info["measured"], "answers": said, "locked": today}
    (record / "before-read.json").write_text(json.dumps(before, indent=1), encoding="utf-8")
    shutil.rmtree(where)
    return house
