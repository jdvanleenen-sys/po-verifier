"""Check 1's group headings. A group is headed by its PO number (or "No PO"); any words after it may
name only items that are rows in that group.

A heading such as "Basic painting, doors, railing, stringers" over a group whose railing row was
$0.00 and whose stringers Sam left off tells the builder he is asked for work that is not on the
request. An item counts as named when every word of its own name (the part before its first comma,
so "Railing, wood" is "railing") is in the heading. Plurals count: "stringers" names "Stringer".
"""
import re

from request_text import NO_HEADING, SUBTOTAL, group_blocks, normalise

WORD = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*")
COLUMN_HEADS = "item unit"


def words(text):
    """The words of a text, lower case, each plural taken as its singular."""
    return {w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
            for w in WORD.findall(normalise(text))}


def own_name(item):
    return words(item.split(",")[0])


def heading_text(block):
    """A group's heading: from its PO number to the table's column heads."""
    ends = [i for i in (block.find(COLUMN_HEADS), block.find(SUBTOTAL)) if i > 0]
    return block[:min(ends)] if ends else block


def heading_problems(request, expected):
    """Each price list item a group heading names that is not a row in that group."""
    items = expected.get("price_items") or []
    problems = []
    for key, (block, _) in group_blocks(request, expected.get("po_numbers"))[0].items():
        if key == NO_HEADING:
            continue
        said = words(heading_text(block))
        rows = [r["item"] for r in expected["rows_on"] if normalise(r["po"]) == key]
        on = set().union(*(words(r) for r in rows))
        named = sorted({item.split(",")[0].strip() for item in items
                        if own_name(item) and own_name(item) <= said and not own_name(item) <= on})
        if named:
            group = "No PO" if key == "none" else "PO " + key.upper()
            problems.append(f"the {group} heading names {', '.join(named)}, not a row in that group. "
                            "Head a group with its PO number only")
    return problems
