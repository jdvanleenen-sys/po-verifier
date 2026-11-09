"""Sam's answer to "attach your notes?", and what the proof must then hold. Used by build_request.py."""
import sys

ONLY = "only:"


def choose_notes(notes, choice):
    """Sam's answer to "attach your notes?": yes (all of them), no, or only:<file>,<file>."""
    if choice == "yes":
        return list(notes)
    if choice == "no":
        return []
    if not choice.startswith(ONLY):
        sys.exit("--notes must be yes, no, or only:<file name>,<file name>. Nothing was built.")
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
