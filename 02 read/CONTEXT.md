# 02 read: turn the documents into rows

## What this stage is for
The AI reads everything in the house's intake folder and writes it out as rows. Sam checks the
rows before anything is compared.

## What comes in
Everything in `../01 intake/<house>/`: each PO, each EPO, Sam's measurements, and the address,
lot, builder and dates he gave. The price list, as described in `../reference/price-list.md`.

**First step, every read-back:** run `python "02 read/prices.py" snapshot <house>` and put the line
it prints in the read-back's front matter as `price list read:`. Match only against that snapshot.

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
account code and notes, and show that match to Sam like any other. Write the match in the EPO
table's "Item it pays for" cell as `row N, <price list item>`: the money gate finds the row by that.
A field the EPO does not print is written "not printed".
Also say which way the money goes. Most EPOs pay Sam. A back charge against Sam takes money from
him. A back charge against another trade, where the builder pays Sam to fix that trade's work,
still pays Sam. Sam confirms the direction with the rest of the table.

## What is read from Sam's measurements
One row per thing he measured, in his own words: what it is, its size or count, the colour, and
anything else he wrote.

A row with no measurement of Sam's at all (a payment-split line, say) has `not in notes; standing
answer, contractor.md` in that cell. When Sam answers an `ask Sam:` cell that is not a number (which
price list row, say), write his words in that row's note in the next read-back, and answer the grid
cell `pass: Sam picked <item> (<date>)`.

Write the "Sam measured" cell as his words in quotes first, then `;`, then the size slot, then
`;` and anything else: `"Railing 13'"; 13 ft; no colour given (photo line 1)`. The size slot holds
one plain number, with "count" before it or a unit after it if you like (', ft, feet, LF, SF,
sq ft, EA, each). After that the code accepts only three things: nothing; a comma and a remark
("3016, Sam confirmed"); or a remark of plain words before its first comma ("0 here, counted on
/027"). A remark may not hold a sign, a number word (one to twenty), a digit (except in a PO
number such as /027), or a word that multiplies (each, both, pair, double, twice, of them). These
limits are on the size slot only; the parts after the next `;` are free notes and may hold digits
("photo line 1"). Code
reads the size only from that slot, the same way in the grid and the money gate, and it also reads
his quoted words: if they multiply the size (10' x2, ×2, each side, both sides, a pair, double,
twice, two of them) the cell reads as no size. In his words, "x" before the size itself ("8' doors
x12" with 12 in the slot) is how he writes a count, and "12' x 12'" (a number with a unit after
it) is a room size; neither counts as a multiplier. The slot must also be backed by his words:
when his quoted words hold a number, the slot must be one of his numbers ("Railing 16'" with 61 in
the slot reads as no size). His quoted words are read for the same traps as the slot: a range
(13-14', 13 to 14), a pointer (see row 3, same, ditto, as above, do.), feet and inches (16 ft 6 in,
16'6"), a number in words with a unit (sixteen feet), or a multiplier (x2, ×2, @, times, (2), 2 of,
each, both, pair, twice) makes the cell read as no size. Quoted words with no number at all do not
back a size, except the exact words "done as ordered" (a standing answer). A cell with no quoted
words ("stringers; 34 ft"), a 0 in the slot and a cell that ends "Sam confirmed" are read from the
slot alone. Anything else reads as
no size. Never write in
the slot a size you worked out: feet and inches (13'6"), a multiplier (124 ft x2, (x2), ×2), a
range (10-12', 13 – 14 ft), a fraction (13 ½ ft), two sizes (13 ft / 16 ft), a number in words
(ten), a row number (see row 3), or a comma for a decimal point (10,5). Write his words as he wrote
them and leave the slot for his answer: the grid reads no size there and asks Sam, and his number
goes in the slot when he gives it.

Every row on a PO is also set against the PO itself (the po-line rule, `po_lines.py`, run by
`grid.py check`): its PO qty, unit price and line total must be printed, in that order, on the PO line that carries
its "line as printed", so copy that line exactly. A qty and unit price swapped (125 x 2.00 for
2 x 125.00, the same total) fails. A row whose PO number is not the ORDER # of any PO in intake
fails too (a 0 missing, as a builder's other system may print it): copy the number from the PO. Only an HTML PO (one table row per line, as
SupplyPro and BuildPro save them) can be read this way; rows on a PDF PO are counted in the check's
output as not checked, and those rows are checked by eye.

The POs read table is set against the POs too (`po_totals.py`, run by `grid.py check`): each row's
subtotal, each tax amount by its name (GST/HST, PST, ...) and the total must be exactly what that
PO's file prints. Copy the tax lines as the PO names them, such as `GST/HST $0.00; PST $225.69`; a
tax the PO prints as $0.00 may be left out. A PO number no file in intake prints is refused. A PO on
a PDF is named in the check's output, and its totals are checked by eye.

The rule grid puts some numbers to Sam by code before anything is priced, because each has cost real
money in testing: a number that may be a thousands figure written with a dot for a comma ("3.016"
for 3,016), a number ten times or more off its PO line, a 0 against a PO line (the whole line becomes
a credit), and the same item, quantity and price on two different POs (probably ordered twice). Ask
him. When he answers, write the number he gave in the row's "Sam measured" cell, after his own
words, and end that cell with "Sam confirmed". Never write "Sam confirmed" for a row he was not
asked about.

## Standing answers: never ask what Sam already answered
Before any question to Sam, read the standing answers in `../reference/contractor.md` (lines not
in his notes, payment splits, builder-named price list rows). When one answers the question, apply
it and do not ask:
- **Lines not in his notes** says done as ordered: write the row's "Sam measured" cell as
  `"done as ordered"; <PO qty>; standing answer, contractor.md`. Its count is the PO's. When the PO
  prints EA on a line the price list prices per foot or per square foot, the PO's number is a size
  only if "How he writes measurements" in contractor.md says so for that kind of line (for example
  "square footage is floor area, as the PO counts it", or "stringers are in feet"); then use it and
  do not ask. If contractor.md does not say, ask Sam what the PO's number counts.
- **Payment splits** names a line: answer its warning `leave unpriced: payment split, standing
  answer, contractor.md`.
- **Builder-named price list rows**: a PO line from that builder that fits the builder's own row
  is matched to it, not listed as "pick one". A note of Sam's that gives no type ("Railing 16'")
  takes the same row when the PO line it sits against was matched to the builder's row; say so in
  the row's note so Sam sees it.
- **When a PO line's own notes cut against a standing answer** (a builder's own railing row, but the
  line says "iron spindle"), keep the standing answer's match and list the row under "At risk for this
  house" with the words from the notes. Do not ask it as a separate question: Sam sees it in the table
  he says yes to, and a standing answer is his answer until he changes it there.
Sam still sees every one of these in the table he says yes to; the standing answer only saves the
question. When the answer says "ask each time", ask. Never ask Sam something his notes, the price
list or an answer he already gave in this house settles.

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
1. **He adds the item to the price list himself,** in Excel (`../reference/price-list.xlsx`). The AI
   then takes a new snapshot, writes a new numbered read-back from it, and matches the item to
   the new row.
2. **He names an existing item** that it should match.
3. **He says leave it unpriced.** It goes to compare marked "not on the price list", with no
   measured value and no call.

His answer in the warning table starts with the way he settled it: `add row`, `names` (the item),
or `leave unpriced`, then his words. Anything else, such as "I don't know, ask Joe", is no answer,
and the house does not leave this stage.

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
8. `python "02 read/prices.py" check <house>` passes: every priced row's item, unit and rate is
   exactly as the snapshot has them.
9. The rule grid passes: `python "02 read/grid.py" check <house>`. See "The rule grid" below.

If check 1, 2, 3, 4 or 6 fails, say which PO and stop. If check 8 fails, fix the row from the
snapshot and run it again; never change the snapshot.

## The rule grid
The grid is the record of the checks above: one cell for every row against every row rule, and
every PO against every PO rule. Code fixes the number of cells before anyone checks anything, so a
check that was skipped shows as a blank cell, and a blank cell is refused.

1. When the read-back's tables are written, run `python "02 read/grid.py" build <house>`. It writes
   `<house>/grid-N.md` beside `read-back-N.md`. Code fills every cell it can work out: line math,
   the PO is read, the price, the unit, the selection, the measured quantity, the subtotal, the tax,
   each PO once, and the vendor. The rest are `?`.
2. Answer the `?` cells **one rule at a time**: take one column, answer it for every row from top
   to bottom, then move to the next column. Do not answer one row across all its rules at once.
   Checking one rule at a time keeps a rule from being missed while you attend to another.
3. Each answer is a status, a colon, and what you looked at, such as `pass: 'railing 22 ft wood' is
   railing, wood, per LF`. The grid's Rules table says who fills each rule; the statuses each rule
   allows are in `02 read/grid_rules.py`. `ask Sam:` goes to Sam with the table. `at risk:` must be
   named under "At risk for this house" on a line that names that trap (unit, selection or notes).
   `not comparable:` is for a PO line that is not a count Sam can measure (see "Careful").
4. Never change a cell code filled. If a code cell is wrong, the read-back is wrong: fix the row,
   rebuild the grid with `--replace` (only while the read-back is a draft), and answer it again.
5. Run `python "02 read/grid.py" check <house>`. It refuses a blank or `?` cell, a missing or extra
   row, a changed code cell, any `fail`, an at-risk row not under At risk, and a read-back whose POs
   read, Rows or Extra items changed after the grid was built. It also refuses a PO made out to
   anyone but the contractor in `../reference/contractor.md` (a different contractor is a different
   copy of the folder, set up through `00 setup`), and any file in `01 intake/<house>/` that changed,
   was added or is gone since `grid.py build` wrote the grid's Intake read table. Never edit that
   table. Intake never changes across read-backs either: every later grid (and its build) is
   checked against the house's first grid, so a PO edited before read-back 2 is refused, not
   fingerprinted afresh.

The house leaves this stage only when `grid.py check <house> --final` passes, which also refuses
any cell still marked `ask Sam`, any warning item with no answer from Sam, and any row marked
"not on the price list" that the warning table leaves out. Sam's answers go into a new numbered read-back with its own grid.
The grid is not Sam's to approve; it is the record of what was checked before he saw the table.

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
Write his yes, name and date into the read-back, then run `python "02 read/seal.py" "02 read/<house>/read-back-N.md"`.
Run it only after `grid.py check <house> --final` passes: the seal records the grid's sha256, and the
grid never changes after it. seal.py runs that check itself and refuses to seal a read-back it
refuses, or one that is not the highest read-back. Never set `status: approved` by hand. If he says "I don't know" about a row, that row's grid cell
says `ask Sam:` and the read-back stays a draft.

Every numbered record has a `from:` line and an `attempt:` line; one without either is refused, at the seal and after. A read-back's `from:` names
exactly one file or folder: `01 intake/<house>/` for read-back 1, and
the read-back it corrects (`02 read/<house>/read-back-1.md`) for each one after. Its `attempt:` is
its file number. A `from:` names a record of this same house, in this stage or an earlier one,
never another house's. compare and the request refuse a record whose `from:`, `attempt:` or
numbering is wrong.

## What goes out
For each attempt, `<house>/grid-N.md`, the rule grid, and `<house>/read-back-N.md` (N starts at 1), holding the confirmed
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
  Copy it as printed, and answer the grid's `count` cell `not comparable:` with why. Sam sees it in
  the table he says yes to; compare lists it apart with no dollars.
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
