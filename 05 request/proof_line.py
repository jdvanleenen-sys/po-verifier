"""Check 5's reading of the request's own "Proof attached." sentence, against the pages attached.

Loop run 5 (2026-11-09): a request said "Site notes not attached." while the build attached the
notes photo, and passed. The sentence is what the builder reads, so it must agree with the proof:
with notes attached it names each notes file (layout: "the site notes of <date> (<file>)"; "the
site notes of <date>" alone names them all only when every notes page is attached); with
notes in intake but none attached it says "Site notes not attached". A notes file Sam left out is
never named.
"""
from request_text import normalise

START = "proof attached"
END = "how to read this"
NOT_ATTACHED = "site notes not attached"
# When every notes page is attached, these words name them all (requests numbered before 2026-11-09
# say "the site measurements of <date>"). When only some are, each is named by its file.
WHOLE = ("site notes of", "site measurements of")


def sentence(request_text):
    """The proof sentence, lower case, or None when the request prints none."""
    text = normalise(request_text)
    start = text.find(START)
    if start < 0:
        return None
    end = text.find(END, start)
    return text[start: end if end > start else start + 600]


def problems(request_text, proof):
    """Every way the proof sentence disagrees with the notes attached."""
    attached, left_out = proof.get("notes_attached", []), proof.get("notes_left_out", [])
    if not attached and not left_out:
        return []
    said = sentence(request_text)
    if said is None:
        return ["the request has no \"Proof attached.\" line; it must say which site notes go with it"]
    every_page = attached and not left_out and any(w in said for w in WHOLE)
    found = [f"the proof line does not name the site notes {n}, which are attached"
             for n in attached if normalise(n) not in said and not every_page]
    found += [f"the proof line names {n}, which Sam left out" for n in left_out if normalise(n) in said]
    if not attached and NOT_ATTACHED not in said:
        found.append("no site notes are attached, so the proof line must say \"Site notes not attached\"")
    if attached and NOT_ATTACHED in said:
        found.append("the proof line says \"Site notes not attached\", but site notes are attached")
    return found
