---
house: 77-mockup-drive
attempt: 1
stage: 02 read
from: 02 read/77-mockup-drive/read-back-1.md
read-back tables sha256: 994af15dd82b72265cc9945771868da63c1b0987310eb801112687b8ea3d1229
---

# 77-mockup-drive, rule grid 1

Built by `02 read/grid.py`. Code filled every cell it can work out. Answer each `?` one
column at a time: take one rule, answer it for every row, then the next rule. Write the
status, a colon, and what you looked at. Never change a cell code filled.

## Rules
| Rule | Question | Filled by |
|---|---|---|
| line-math | PO qty x unit price = line total, as printed | code |
| po-read | The row's PO is in POs read, or a no-PO row is named under Extra items | code |
| price | Item, unit and rate are exactly as on the price list snapshot | code |
| unit | The unit printed on the PO is the price list unit (if not: At risk) | code |
| selection | The selection printed under the line agrees with the PO qty (if not: At risk) | code |
| measured | A size or count was read from Sam's notes | code |
| po-line-match | The PO line, as printed, is this price list item | AI |
| note-match | Sam's note, read with the price list only, is this price list item | AI |
| line-notes | The notes under the line do not change what it covers (if they do: At risk) | code finds notes, AI answers |
| count | Sam's quantity can be set against the PO qty (not a lump sum or a part) | AI |
| lines-subtotal | The line totals add up to the printed subtotal | code |
| tax-total | Subtotal plus the tax lines equals the printed total | code |
| once | The PO number appears once in POs read | code |
| vendor | Every PO is to the same vendor | code |
| address | The job address matches the address Sam gave | AI |

## Row grid
| # | line-math | po-read | price | unit | selection | measured | po-line-match | note-match | line-notes | count |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | pass: 1 x 1000 = 1000 | pass: MKR-02402401/012 is in POs read | pass: EA at 1000 on the snapshot | pass: printed EA, price list EA | pass: selection 1, qty 1 | pass: 1 | pass: Wall Prime, EA, qty 1 at $1000.00 is the flat-rate wall prime | pass: 'prime 1' is one flat-rate wall prime | n/a: no notes under the line | pass: count 1 against PO qty 1 |
| 2 | pass: 3020 x 2.75 = 8305 | pass: MKR-02402401/027 is in POs read | pass: Floor SF at 2.75 on the snapshot | at risk: printed EA on a line the price list prices per Floor SF | pass: selection 3020, qty 3020 | pass: 3020 | pass: Interior Paint & Stain - Finished Areas at $2.75 a floor foot is basic SF painting; community is Single Family | pass: '3020 sf' read as floor area; Sam confirms (At risk) | at risk: 'Garage not included (added separately if selected)' puts the garage outside this line | pass: 3020 floor SF against PO qty 3020 |
| 3 | pass: 7 x 60 = 420 | pass: MKR-02402401/027 is in POs read | pass: EA at 60 on the snapshot | pass: printed EA, price list EA | at risk: qty 7, selection 1; both recorded | pass: 12 | pass: 8' Doors & Trim, EA, is 8' doors and trim | pass: '8' doors x12' is each door with its trim | n/a: no notes under the line | pass: 12 doors against PO qty 7 |
| 4 | pass: 22 x 38 = 836 | pass: MKR-02402401/027 is in POs read | pass: LF at 38 on the snapshot | pass: printed LF, price list LF | at risk: qty 22, selection 1; both recorded | pass: 22 | pass: Interior Railing - Wood, LF, is railing, wood, not handrail | pass: 'railing 22 ft wood' is railing, wood, per LF | n/a: no notes under the line | pass: 22 LF against PO qty 22 |
| 5 | pass: 30 x 9 = 270 | pass: MKR-02402401/027 is in POs read | pass: LF at 9 on the snapshot | pass: printed LF, price list LF | at risk: qty 30, selection 1; both recorded | pass: 34 | pass: Stair Stringers, LF, is stringer, inside or outside | pass: 'stringers 34 ft' is stringer, per LF | n/a: no notes under the line | pass: 34 LF against PO qty 30 |
| 6 | pass: 1 x 500 = 500 | pass: MKR-02402401/041 is in POs read | pass: EA at 500 on the snapshot | pass: printed EA, price list EA | pass: selection 1, qty 1 | pass: 1 | pass: Interior Paint Touchup, EA, qty 1, is the flat-rate touch-up | pass: 'touch up 1' is one flat-rate touch-up | n/a: no notes under the line | pass: count 1 against PO qty 1 |
| 7 | n/a: on no PO | pass: on no PO, named under Extra items | pass: SF at 1.6 on the snapshot | n/a: on no PO | n/a: on no PO | pass: 420 | n/a: on no PO | pass: 'GARAGE - primed and painted incl ceiling, 420 sf' is prime and paint garage, including ceiling, per SF | n/a: on no PO | n/a: on no PO, set against 0 |

## PO grid
| PO number | lines-subtotal | tax-total | once | vendor | address |
|---|---|---|---|---|---|
| MKR-02402401/012 | pass: 1000 = 1000 | pass: 1000 + 50 = 1050 | pass: listed once | pass: every PO is to Sample Painting Co., V00999 (attn Office) | pass: prints 77 Mockup Drive, Sampleton, AB T0X 0X0; Sam gave 77 Mockup Drive |
| MKR-02402401/027 | pass: 8305 + 420 + 836 + 270 = 9831 | pass: 9831 + 491.55 = 10322.55 | pass: listed once | pass: every PO is to Sample Painting Co., V00999 (attn Office) | pass: prints 77 Mockup Drive, Sampleton, AB T0X 0X0; Sam gave 77 Mockup Drive |
| MKR-02402401/041 | pass: 500 = 500 | pass: 500 + 25 = 525 | pass: listed once | pass: every PO is to Sample Painting Co., V00999 (attn Office) | pass: prints 77 Mockup Drive, Sampleton, AB T0X 0X0; Sam gave 77 Mockup Drive |

## Intake read
Every file in `01 intake` when this grid was built. Written by `grid.py`; never edit it. A request is refused if any of these changes.

| File | sha256 |
|---|---|
| `house-info.md` | fd66a970a4549794a796f57ddc71f9bde2e5946664d3aeb111e35ce4dba480f6 |
| `PO MKR-02402401-012.html` | 503ed02f13eb0b0c8dc79e5788840620bc73724146f305d8c07771283d82b44f |
| `PO MKR-02402401-027.html` | e5e16c23df55b99b881a3dd13172d740d1de487ac2f746f5d726f177ad3c0f2f |
| `PO MKR-02402401-041.html` | 1c1350f239462ba8f4a81240b3107ba595d2caad1eef01fcad8a1c1eb23f6548 |
| `site-notes.txt` | a8681b67f99c2d7ed39f3156c7853d301e673bd9d3a9125872227e5aaced54f7 |
