"""The open questions in a draft read-back, as cards for the Check screen, and Sam's card answers
as plain lines for the agent's next read-back. Code reads only the tables the stage fixes (the
warning table, Pick one, the Rows table and the rule grid); it never reads the AI's prose for them."""
import hashlib

from folder import highest

ASK = "ask sam:"
ANSWERED = ("add row", "names", "name ", "leave unpriced")
COLUMNS = {"line": "line as printed", "po": "po number", "qty": "po qty", "measured": "sam measured"}


def _tables(folder):
    return folder.script("02 read", "grid_read")


def _rows(gr, text):
    """The read-back's Rows table, keyed by row number."""
    return {r.get("#", ""): r for r in gr.as_dicts(gr.under(text, "rows"))}


def _warnings(gr, text):
    header, rows = gr.table(gr.under(text, "warning"))
    cards = []
    for cells in rows:
        answer = cells[-1].strip().lower() if len(cells) == len(header) else ""
        if answer.startswith(ANSWERED):
            continue
        item = dict(zip(header, cells))
        cards.append({"id": f"warning:{cells[0]}:{cells[1]}", "kind": "warning", "po": cells[0],
                      "title": cells[1], "detail": item.get("qty and unit", ""),
                      "closest": item.get("closest items", "")})
    return cards


def _picks(gr, text, rows):
    header, found = gr.table(gr.under(text, "pick one"))
    cards = []
    for cells in found:
        if len(cells) >= len(header) and cells[-1].strip():
            continue
        row = rows.get(cells[0], {})
        cards.append({"id": f"pick:{cells[0]}", "kind": "pick", "row": cells[0],
                      "title": row.get(COLUMNS["line"], f"Row {cells[0]}"), "po": row.get(COLUMNS["po"], ""),
                      "options": [c for c in cells[1:3] if c]})
    return cards


def _asks(gr, grid_text, rows, picked):
    """One card per row with ask Sam cells, unless a Pick one card already asks about that row."""
    header, found = gr.table(gr.under(grid_text, "row grid"))
    cards = []
    for cells in found:
        asks = {header[i]: c.split(":", 1)[1].strip() for i, c in enumerate(cells)
                if i < len(header) and c.lower().startswith(ASK)}
        if cells[0] in picked:
            asks.pop("price", None)
        if not asks:
            continue
        row = rows.get(cells[0], {})
        kind = "number" if "measured" in asks else "other"
        cards.append({"id": f"row:{cells[0]}", "kind": kind, "row": cells[0],
                      "title": row.get(COLUMNS["line"], f"Row {cells[0]}"), "po": row.get(COLUMNS["po"], ""),
                      "read": row.get(COLUMNS["measured"], ""), "po_qty": row.get(COLUMNS["qty"], ""),
                      "why": "; ".join(f"{rule}: {why}" for rule, why in asks.items())})
    return cards


def _prose_asks(text):
    """An "ask Sam:" the read wrote outside a table (under Checks run, say). The folder's final check
    does not block on these, so the app shows each one rather than let it pass unseen."""
    cards = []
    for line in text.splitlines():
        plain = line.strip()
        if plain.startswith("|") or ASK not in plain.lower():
            continue
        at = plain.lower().index(ASK)
        topic = plain[:at].strip(" -:*`") or "A question from the read"
        cards.append({"id": "prose:" + hashlib.sha256(plain.encode("utf-8")).hexdigest()[:12], "kind": "other",
                      "row": None, "title": topic, "why": plain[at + len(ASK):].strip(), "po": ""})
    return cards


def cards(folder, house):
    """Every open question in the house's highest read-back, or [] when none is open."""
    where = folder.stage("02 read", house)
    read_back = highest(where, "read-back")
    if read_back is None:
        return []
    gr = _tables(folder)
    text = read_back.read_text(encoding="utf-8")
    grid = where / read_back.name.replace("read-back", "grid")
    grid_text = grid.read_text(encoding="utf-8") if grid.is_file() else ""
    rows = _rows(gr, text)
    picks = _picks(gr, text, rows)
    asks = _asks(gr, grid_text, rows, {p["row"] for p in picks})
    return _warnings(gr, text) + picks + asks + _prose_asks(text)


def answer_lines(open_cards, answers):
    """Sam's answers as lines for the next read-back. answers maps card id to {"choice", "words"}.
    Every open card must be answered; an unknown card id is refused."""
    by_id = {c["id"]: c for c in open_cards}
    unknown = set(answers) - set(by_id)
    if unknown:
        raise ValueError("Those questions are out of date. Reload the screen.")
    missing = [c["title"] for c in open_cards if c["id"] not in answers]
    if missing:
        raise ValueError("Answer every card first: " + "; ".join(missing))
    return [_line(by_id[key], value) for key, value in answers.items()]


def _line(card, value):
    choice, words = value.get("choice", ""), " ".join(str(value.get("words", "")).split())
    if card["kind"] == "warning":
        said = {"leave": "leave unpriced", "names": f"names {words}"}.get(choice)
        if not said or (choice == "names" and not words):
            raise ValueError(f"{card['title']}: leave it unpriced, or name the price list item.")
        return f"- Warning item {card['po']} '{card['title']}': Sam: \"{said}\""
    if card["kind"] == "pick":
        if choice not in ("0", "1") or int(choice) >= len(card["options"]):
            raise ValueError(f"{card['title']}: pick one of the two items.")
        return f"- Pick one, row {card['row']}: Sam picked \"{card['options'][int(choice)]}\""
    if card["kind"] == "number" and choice == "right":
        return f"- Row {card['row']}: Sam: \"Right, that is what I measured.\""
    if not words:
        raise ValueError(f"{card['title']}: give your answer.")
    if card["row"] is None:
        return f"- {card['title']} (the read asked: {card['why']}): Sam: \"{words}\""
    return f"- Row {card['row']} ({card['why']}): Sam: \"{words}\""
