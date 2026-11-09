"""Sam's answer to "attach your notes?", and what the proof must then hold. Used by build_request.py."""
import re
import sys
from pathlib import Path

ONLY = "only:"
OTHER_HOUSE = "yes-other-house"
# house-info.md says so when the notes page also holds another house's notes ("It covers two houses").
SHARED = re.compile(r"\b(?:covers|holds|has|shows)\s+(?:two|2|both)\s+houses\b|\banother house\b|\bother house\b", re.I)


def other_house(intake_folder):
    """True when house-info.md says the notes page also holds another house."""
    info = Path(intake_folder) / "house-info.md"
    return bool(info.is_file() and SHARED.search(info.read_text(encoding="utf-8-sig", errors="replace")))


def choose_notes(notes, choice, shared=False):
    """Sam's answer to "attach your notes?": yes (all of them), no, only:<file>,<file>, or, when the
    notes page also holds another house, yes-other-house (all of them, knowing the builder sees the
    other house's notes). A plain yes cannot send another house's notes by accident (loop run 5)."""
    if choice == "no":
        return []
    if shared and choice != OTHER_HOUSE:
        sys.exit("house-info.md says the notes page also holds another house, so the builder would see that "
                 "house's notes too. Ask Sam in those words. If he still says attach it, build with "
                 f"--notes {OTHER_HOUSE}; otherwise --notes no. Nothing was built.")
    if choice in ("yes", OTHER_HOUSE):
        return list(notes)
    if not choice.startswith(ONLY):
        sys.exit(f"--notes must be yes, no, {OTHER_HOUSE}, or only:<file name>,<file name>. Nothing was built.")
    names = [n.strip() for n in choice[len(ONLY):].split(",") if n.strip()]
    by_name = {p.name: p for p in notes}
    missing = [n for n in names if n not in by_name]
    if missing or not names:
        sys.exit(f"Sam named notes that are not in intake: {', '.join(missing) or '(none named)'}. "
                 f"The notes files are: {', '.join(by_name) or 'none'}. Nothing was built.")
    return [by_name[n] for n in names]


def proof_spec(expected, attached, notes):
    """What must be in the proof, and the notes pages Sam left out, which must not be."""
    names = [p.name for p in attached]
    return {"po_numbers": expected["po_numbers"], "epo_names": expected["epo_names"],
            "notes_attached": names, "notes_left_out": [p.name for p in notes if p.name not in names]}
