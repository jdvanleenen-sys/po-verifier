---
type: reference
doc: price-list-source
checked: 2026-10-15
---

# Price list: where it lives and how to read it

**What this is for:** any stage that prices an item reads this first, so every rate comes from
one place.

**Where this folder stands:** a practice build. It is not connected to live invoicing, and
nothing here is sent to anyone.

## Where it lives
- Airtable base: **Summit Coat Painting (DEMO)** (base ID kept private)
- Table: **Price List** (table ID kept private)
- One row per item. 50 rows in Airtable on Oct 15, 2026 (53 in the CSV copy below); Active ("Whole-house interior" is not).
  The last three (wall prime, touch-up, 8' doors and trim) were added to `price-list.csv` on
  Oct 15. They are **not yet in Airtable**. Until they are, read the CSV, or those three items will
  show as not on the price list.
- The rates are made up for the demo. The item names and units follow a real painter's price
  sheet, so practice POs will not always find a match.
- The base has other tables (Jobs, Clients, Line Items, POs, Approvals). This build reads only
  Price List.

## The fields

| Field | What it is |
|---|---|
| Item | The name of the work |
| Unit | Floor SF, SF, LF, EA, per room, per kitchen, Hours or Incl. |
| Rate | The agreed rate, in dollars per unit |
| Active | Ticked means it is on the current sheet. Empty means it is not. |

What the units mean (from the table's own field description):
- **Floor SF** is the house's floor area.
- **SF** is surface area, the area actually painted.
- **LF** is linear feet. A PO or a note that says FT or "ft" means the same thing.
- **EA** is each.
- **per room**, **per kitchen** and **Hours** are counted as written.
- **Incl.** is included at no charge (rate $0).

## The copy in this folder
`reference/price-list.csv` is a copy of the Price List table, exported Oct 15, 2026, plus the
three rows above (53 rows, columns Item, Unit, Rate, Active). **For now, read the CSV, with or
without a connector.** Once the three rows are in Airtable, Airtable becomes the one to read and
this line changes. Every rule on this page applies to the CSV the same way.

## How to read it
- From `price-list.csv` for now (see above). From Airtable, read only, once it has the three rows.
- Use only rows with Active ticked.
- Match on Item. Use the Rate exactly as written. Do not round it.
- Read it fresh at `02 read` for each house. Record the item, unit and rate on each row of the
  read-back, and the date it was read once at the top. Later stages use those recorded rates, not a
  new read.

## Must not
- **Do not change, add or delete a row.** Only the painter changes the price list. If a rate
  looks wrong, say which one and stop.
- **Do not price from the rate printed on a PO.** Use this table. This rule exists because
  builder POs arrive at old or wrong rates, and pricing from them hides the difference the compare
  is there to find.
- **Do not use a rate from memory or from an earlier run.** This rule exists because rates
  change, and POs keep arriving at the old one.
- **Do not pick the nearest item when there is no match.** List the item as "not on the price
  list" and raise the warning in `02 read/CONTEXT.md`. The painter adds the row in Airtable
  himself, names an existing item, or says leave it unpriced.
- **Do not read or write any other table in this base.** It holds a separate demo's jobs and
  POs; mixing them in would put another job's numbers in this one.
- **No API key or access token goes in this folder.** The connector handles the login.

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
A rate has been read correctly when the output row names the Item exactly as the table has it,
gives its unit and its rate, and says the date the table was read.

## Later: the real price list
When this build is pointed at real jobs, the price list is the Price List table in the painter's
own Airtable base. Nothing in this practice build reads or changes
that base.
