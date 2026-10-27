# 02 read: turn the documents into rows

## What this stage is for
The AI reads everything in the house's intake folder and writes it out as rows. Sam checks the
rows before anything is compared.

## What comes in
Everything in `../01 intake/<house>/`: each PO, each EPO, Sam's measurements, and the address,
lot, builder and dates he gave. The price list, as described in `../reference/price-list.md`.

## What is read from each PO
All of it, copied exactly as printed.
- **The PO number** (printed as ORDER #). It goes on every row read from that PO and follows
  the row through every later stage. It is how the builder finds the PO.
- About the PO: builder, community, cost code, vendor name and number, job name,
  job address, lot/block/unit, plan, elevation, date needed, price effective date, who submitted
  it and when, who approved it and when (if filled in).
- Each line: option number, SKU, description, unit, quantity, unit price, line total.
- Under each line: the special option information, every line of it. That means the option name,
  each selection, and any notes.
- The money at the bottom: subtotal, each tax line, total.

## What is read from each EPO
All of it, copied exactly as printed: who created it, community, job name, lot number, legal
lot and block, EPO name, EPO total, reason code, notes, account code, trade partner, date
requested, and its approval status. The EPO name carries the vendor number and the PO number it is
against. Record that PO number on the EPO row. An EPO has a total and no lines, so match it to the item it pays for, using its
account code and notes, and show that match to Sam like any other.
Also say which way the money goes. Most EPOs pay Sam. A back charge against Sam takes money from
him. A back charge against another trade, where the builder pays Sam to fix that trade's work,
still pays Sam. Sam confirms the direction with the rest of the table.

## What is read from Sam's measurements
One row per thing he measured, in his own words: what it is, its size or count, the colour, and
anything else he wrote.

## What each document is evidence for
Each document is good evidence for one thing only. Read each for its own job.

| Document | Use it for | Never use it for |
|---|---|---|
| Builder PO | What the builder ordered and will pay: items, quantities, amounts | The agreed rate, or what Sam's note means |
| Builder EPO | Extra money the builder has already issued, and which PO it is against | Quantities |
| Sam's site notes | What is actually there: the quantity | Rates |
| The price list | The agreed rate and unit | Quantities, or what the builder ordered |

Match Sam's notes to the price list using the note and the price list only. Do not look at the POs
to decide what a note means. The compare has to be independent, or the PO's wording decides the
answer the compare is there to check.

## Matching to the price list
Each PO line and each thing Sam measured is matched to one item on the price list. The match is
shown in the table so Sam confirms it with everything else.
- **Could fit two items:** list it as "pick one", name both items, and Sam decides.
- **Fits no item:** list it as "not on the price list" and raise the warning below.

## Warning: not on the price list
When anything fits no item, put this warning **above** the table, before anything else, so it
cannot be missed:

> **WARNING: not on the price list (N items).** These cannot be priced until each one is
> settled. Nothing moves to compare until then.

Under it, one line per item: the PO number (or "none" for an item only in Sam's notes), the
description as printed, its quantity and unit, and the closest price list items, if any, so Sam
can see why they did not fit. Never show the PO's own rate as the suggested rate. The rate is
Sam's to set.

Sam settles each one in one of three ways:
1. **He adds the item to the Airtable price list himself.** The AI then reads the price list
   again and matches the item to the new row.
2. **He names an existing item** that it should match.
3. **He says leave it unpriced.** It goes to compare marked "not on the price list", with no
   measured value and no call.

The AI never adds, changes or suggests a rate for a price list row. Sam's yes on the table does
not settle a warning item. Each one needs its own answer.

## What is checked before Sam sees it
1. Each line's quantity times its unit price equals its line total.
2. The lines add up to the subtotal printed on the PO.
3. The subtotal plus the taxes equals the total.
4. The job address on each PO matches the address Sam gave.
5. Anything on Sam's notes that is on no PO is an extra item. Each one is a row in the Rows table
   with PO number `none` (the request script reads only that table), and is named again under
   "Extra items".
6. No PO number appears twice in the house folder. If one does, say which and stop. The same PO
   read twice would count its money twice. If Sam says it is the same PO saved twice, read it once,
   leave both files in intake, and write his answer under this check in the read-back. (The
   request script attaches a file saved twice only once.)
7. Every PO line and every measured item matches a price list item. Any that does not raises
   the warning above. The table is still shown, but the house does not leave this stage until
   every warning item is settled.

If check 1, 2, 3, 4 or 6 fails, say which PO and stop.

## At risk for this house
Above the table Sam confirms, list each trap from "Careful" below and from "Careful" in
`../reference/price-list.md` that applies to this house, one line each: the trap, the rows it
touches, and what was done about it. For example: "Unit printed EA on a line priced per square
foot. Row 2. Copied as printed; Sam confirms the 3020 is floor area." A trap that does not apply is
left off. This is where Sam looks first.

## How Sam confirms
He sees one table of everything that was read and replies yes. If a row is wrong, he gives the
right number and the AI writes a new numbered read-back with that row fixed, then shows the table
again. Only a plain yes closes this stage (see "What counts as Sam's yes" in `../CONTEXT.md`).

## What goes out
One file per house in this folder, `<house>/read-back-N.md` (N starts at 1), holding the confirmed
rows, Sam's answer to each warning item, Sam's yes, his name, and the date. Each row that matched
the price list also records the item name, unit and rate exactly as read. The date the price list
was read is recorded once, at the top, because it is read once per read-back. Those are the rates
Sam confirmed, and they are the ones compare uses. Copy the form in `../templates/read-back.md`. The compare stage (`../03 compare/`)
works from the highest-numbered read-back and nothing else.

## What must never happen here
The AI never guesses a number it cannot read. It never corrects a PO, even an obvious mistake.
It never changes the files in intake. Nothing is priced or compared here.

## Careful
These come from real builder POs.
- **The lines add up to the subtotal, not the total.** The total includes tax.
- **A quantity is not always a count.** One PO had a quantity of 0.1 against a lump-sum price.
  Copy it as printed.
- **The unit can be wrong.** One PO said EA on a line that was plainly priced per square foot.
  Copy the unit as printed and say so in the table.
- **The quantity and the selection can disagree.** One line had a quantity of 721 and a selection
  of 773. Record both. Do not pick one.
- **The notes under a line can change what it covers.** One said what the price does not include.
  Copy them in full.
- **A number can be printed oddly.** A selection of 1 can appear as `1.000000000000000e+000`.
- **One house has many POs to many trades.** The order number is the job number, a slash, and a
  running number. Every PO in a house folder should be to the same vendor.
- **Each PO has its own price effective date.** Record it. It says which price list the builder
  priced from.
