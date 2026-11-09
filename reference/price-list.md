---
type: reference
doc: price-list-source
checked: 2026-11-02
---

# Price list: where it lives and how to read it

**What this is for:** any stage that prices an item reads this first, so every rate comes from
one place.

**Where this folder stands:** a practice build. It is not connected to live invoicing, and
nothing here is sent to anyone.

## Where it lives
**`reference/price-list.xlsx`, and nowhere else.** An Excel workbook. The checker reads the sheet
named **Price list**: one row per item, with the columns Item, Unit, Rate, Active first. Any column
after those (such as Source, where a rate came from) is Sam's and is ignored. The demo list has 53
rows, 52 active ("Whole-house interior" is not). Sam opens the file in Excel, changes a rate or
adds a row, and saves it as it is. Nobody else changes it. Each house freezes a plain-text copy
(`02 read/<house>/price-list-N.csv`) when it is read, so a later change never changes a house
already checked.

- The rates are made up for the demo. The item names and units follow a real painter's price
  sheet, so practice POs will not always find a match.
- No login, connector or account is needed to read it, so anyone testing the folder has it.
- Why Excel (Jeff, 2026-11-08): the painter keeps his own list where he can open and edit it, and
  this is how the folder runs from now on, not through Airtable. Later, other software he uses can
  point at the same one file.
- Why a file and not a database (Jeff, 2026-11-02): a database made every tester need access to
  it, and the folder needs one price list, not a system. If Sam's list later lives in a database,
  an export to this file keeps everything below the same.

## The fields

| Field | What it is |
|---|---|
| Item | The name of the work |
| Unit | Floor SF, SF, LF, EA, per room, per kitchen, Hours or Incl. |
| Rate | The agreed rate, in dollars per unit |
| Active | TRUE means it is on the current sheet. FALSE or empty means it is not. |

What the units mean:
- **Floor SF** is the house's floor area.
- **SF** is surface area, the area actually painted.
- **LF** is linear feet. A PO or a note that says FT or "ft" means the same thing.
- **EA** is each.
- **per room**, **per kitchen** and **Hours** are counted as written.
- **Incl.** is included at no charge (rate $0).

## How to read it
Code reads the file. At `02 read`, before matching anything, run:

```
python "02 read/prices.py" snapshot <house>
```

It checks the file (four columns, a number in every rate, a known unit, no item active twice, and no two active items whose names differ only by a dash, a space or capitals; a comma in a rate only between thousands, so 24,50 is refused: write 24.50)
and copies it unchanged to `02 read/<house>/price-list-N.csv`. It prints one line; put that line
in the read-back's front matter as `price list read:`. That copy is the price list for this
read-back. Then:

- Use only rows with Active TRUE.
- Match on Item, and copy the Item, Unit and Rate exactly as the snapshot has them. Do not round.
- Before showing Sam the table, run `python "02 read/prices.py" check <house>`. It refuses any
  row whose item, unit or rate differs from the snapshot. The money gate runs the same check
  again before any request is numbered.
- Later stages use the rates recorded in the read-back, never a new read.

If the snapshot command refuses the file, tell Sam what it said and stop. He fixes it in Excel.

## Must not
- **Do not change, add or delete a row.** Only Sam changes the price list. If a rate looks wrong,
  say which one and stop.
- **Do not price from the rate printed on a PO.** Use this list. Builder POs arrive at old or
  wrong rates, and pricing from them hides the difference the compare is there to find.
- **Do not use a rate from memory or from an earlier run.** Rates change, and POs keep arriving
  at the old one.
- **Do not pick the nearest item when there is no match.** List the item as "not on the price
  list" and raise the warning in `02 read/CONTEXT.md`.
- **Do not edit a snapshot.** If the price list changes, that is a new snapshot and a new
  read-back.

## Careful
- **Handrail and railing are different rows**, at very different rates. Railing also comes as
  wood, metal and 2-tone.
- **Floor SF and SF are different measures.** A builder's square footage on an interior paint
  line is usually floor area; a garage or a high wall is priced on painted surface. Sam confirms
  which one his number is.
- **Single family and multi family have separate basic painting rows.** Use the PO's community or
  job type to tell which, and show the choice to Sam.
- **Flat-rate prime and touch-up are their own rows** ("Wall prime, flat rate" and "Interior
  paint touch-up, flat rate"), each EA. They are not part of "Basic SF Painting".
- **"8' doors and trim" is painting the door and its trim, each.** "Upgrade std door to 8'" is an
  extra charge on top of it, not the same item.

## Done when
`python "02 read/prices.py" check <house>` passes on the read-back Sam is about to see.
