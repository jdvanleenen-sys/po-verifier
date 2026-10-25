---
house: 77-mockup-drive
attempt: 1
stage: 02 read
from: 01 intake/77-mockup-drive/
status: approved
price list read: 2026-10-17, from reference/price-list.csv (Airtable export of 2026-10-15 plus the three added rows; 53 rows, 52 active)
---

# 77-mockup-drive, read-back 1

Copy to `02 read/<house>/read-back-N.md`. Stays `draft` until Sam's plain yes is written below.

No item is "not on the price list", so there is no warning. No row needed a "pick one".

## The house
Address, lot, builder, community, job name, plan, date measured, date dropped in:
77 Mockup Drive (Sampleton, AB T0X 0X0 on the POs); lot 24, block 3 (POs: 24/3/); Sample Builder Ltd.;
community Mockup Ridge Single Family (from the PO headers); job name MKR-02402401-77 Mockup Drive;
plan MAPLE-002 - Maple, elevation L; measured 2026-10-02; dropped in 2026-10-14.

## At risk for this house
- Unit printed EA on a line priced per square foot: row 2 (PO MKR-02402401/027, Interior Paint & Stain - Finished Areas, EA, 3020 x $2.75). Copied as printed; matched to the Floor SF row. Sam confirms his 3020 sf is floor area.
- Floor SF vs SF: rows 2 and 7. Sam's "3020 sf" is read as floor area (Floor SF row); his garage "420 sf" is read as painted surface (SF row, "Prime and paint garage, including ceiling"). Sam confirms which measure each number is.
- Single family vs multi family basic painting: row 2. The PO community is "Mockup Ridge Single Family", so the SINGLE FAMILY row ($2.75) was used, not MULTI FAMILY ($2.60). Shown here for Sam.
- Handrail vs railing: row 4. Sam wrote "railing 22 ft wood" and the PO says "Interior Railing - Wood"; matched to "Railing, wood" ($38/LF), not "Handrail" ($10/LF).
- 8' doors and trim vs Upgrade std door to 8': row 3. Sam's "8' doors x12" is the door and its trim, each; matched to "8' doors and trim" ($60/EA). "Upgrade std door to 8'" ($30/EA) is an extra charge on top and was not used.
- Flat-rate prime and touch-up are their own rows: rows 1 and 6. Matched to "Wall prime, flat rate" and "Interior paint touch-up, flat rate", not to Basic SF Painting.
- Quantity and selection disagree: rows 3, 4, 5 (and 1, 6). Quantities 7, 22, 30 sit against a printed selection of `1.000000000000000e+000`. Both recorded; neither picked.
- Notes under a line change what it covers: row 2 says "Garage not included (added separately if selected)". Copied in full. The garage Sam measured (row 7) is on no PO.
- FT means LF: rows 4 and 5. Sam wrote "ft"; read as LF.

## POs read
| PO number | Cost code | Vendor | Job name and address | Lot/block/unit | Plan, elevation | Date needed | Price effective date | Submitted by, when | Approved by, when | Subtotal | Tax lines | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MKR-02402401/012 | PAIN-005 | Sample Painting Co., V00999 (attn Office) | MKR-02402401-77 Mockup Drive; 77 Mockup Drive, Sampleton, AB T0X 0X0 | 24/3/ | MAPLE-002 - Maple, L | 08/25/2026 | 07/15/2026 | Purchasing Desk, 08/20/2026 2:41:07 PM | blank | $1000.00 | GST/HST $50.00; PST $0.00 | $1050.00 |
| MKR-02402401/027 | PAIN-010 | Sample Painting Co., V00999 (attn Office) | MKR-02402401-77 Mockup Drive; 77 Mockup Drive, Sampleton, AB T0X 0X0 | 24/3/ | MAPLE-002 - Maple, L | 09/10/2026 | 07/15/2026 | Purchasing Desk, 09/03/2026 10:12:55 AM | blank | $9831.00 | GST/HST $491.55; PST $0.00 | $10322.55 |
| MKR-02402401/041 | PAIN-020 | Sample Painting Co., V00999 (attn Office) | MKR-02402401-77 Mockup Drive; 77 Mockup Drive, Sampleton, AB T0X 0X0 | 24/3/ | MAPLE-002 - Maple, L | 10/06/2026 | 07/15/2026 | Purchasing Desk, 10/01/2026 4:03:19 PM | blank | $500.00 | GST/HST $25.00; PST $0.00 | $525.00 |

All three: builder Sample Builder Ltd., community Mockup Ridge Single Family, from 100 Example Way, Sampleton, AB T0X 0X0; questions to Purchasing Desk, purchasing@samplebuilder.example. Each is marked "[practice copy]".

## EPOs read (write "none in the folder" if none)
none in the folder

## Rows
| # | PO number | Line as printed | Unit as printed | PO qty | Unit price | Line total | Special option info | Sam measured (his words, size or count, colour, notes) | Price list item | Unit | Rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MKR-02402401/012 | (5120) 09900/005S - Wall Prime | EA | 1 | $1000.00 | $1000.00 | Option Name: Maple; Selection: 1.000000000000000e+000 | "prime 1"; count 1; no colour given | Wall prime, flat rate | EA | 1000 |
| 2 | MKR-02402401/027 | (5120) 09900/010S - Interior Paint & Stain - Finished Areas | EA (priced per square foot; see At risk) | 3020 | $2.75 | $8305.00 | Option Name: Maple; Selection: 3020; Notes: Garage not included (added separately if selected) | "3020 sf"; 3020; no colour given | Basic SF Painting, prime and 2 coat, SINGLE FAMILY | Floor SF | 2.75 |
| 3 | MKR-02402401/027 | (5120) 09900/030S - 8' Doors & Trim | EA | 7 | $60.00 | $420.00 | Option Name: Maple; Selection: 1.000000000000000e+000 | "8' doors x12 (they added the basement ones)"; count 12; no colour given | 8' doors and trim | EA | 60 |
| 4 | MKR-02402401/027 | (5120) 09900/020S - Interior Railing - Wood | LF | 22 | $38.00 | $836.00 | Option Name: Maple; Selection: 1.000000000000000e+000 | "railing 22 ft wood"; 22 ft; no colour given | Railing, wood | LF | 38 |
| 5 | MKR-02402401/027 | (5120) 09900/025S - Stair Stringers | LF | 30 | $9.00 | $270.00 | Option Name: Maple; Selection: 1.000000000000000e+000 | "stringers 34 ft"; 34 ft; no colour given | Stringer, inside or outside | LF | 9 |
| 6 | MKR-02402401/041 | (5120) 09900/500S - Interior Paint Touchup | EA | 1 | $500.00 | $500.00 | Option Name: Maple; Selection: 1.000000000000000e+000 | "touch up 1"; count 1; no colour given | Interior paint touch-up, flat rate | EA | 500 |
| 7 | none | (on no PO) | | | | | | "GARAGE - primed and painted incl ceiling, 420 sf. site super asked for it, said a change order was coming. never saw one."; 420 sf; no colour given | Prime and paint garage, including ceiling | SF | 1.6 |

Sam's notes were matched to the price list from the note and the price list only; the PO lines were matched separately, and the two meet on the price list item. The community used to choose the single family row on row 2 comes from the PO header, as `reference/price-list.md` directs.

Site notes header, as written: "77 Mockup Dr / lot 24", "Oct 2".

## Extra items (in Sam's notes, on no PO)
- Row 7: garage, primed and painted including ceiling, 420 sf. Site super asked for it; Sam never saw the change order. PO MKR-02402401/027 notes say "Garage not included (added separately if selected)".

## Checks run
Run by a script (`read_checks.py`, in the session's scratch space, not this folder; Decimal arithmetic), 2026-10-17.
- 1. Quantity x unit price = line total: pass: 1 x 1000.00 = 1000.00; 3020 x 2.75 = 8305.00; 7 x 60.00 = 420.00; 22 x 38.00 = 836.00; 30 x 9.00 = 270.00; 1 x 500.00 = 500.00. All equal the printed totals.
- 2. Lines add to the subtotal: pass: /012 1000.00 = 1000.00; /027 8305 + 420 + 836 + 270 = 9831.00 = 9831.00; /041 500.00 = 500.00.
- 3. Subtotal + taxes = total: pass: /012 1000.00 + 50.00 + 0.00 = 1050.00; /027 9831.00 + 491.55 + 0.00 = 10322.55; /041 500.00 + 25.00 + 0.00 = 525.00.
- 4. Job address matches the address Sam gave (77 Mockup Drive): pass: all three POs print 77 Mockup Drive, Sampleton, AB T0X 0X0.
- 5. Items in Sam's notes on no PO listed as extra: pass: one extra item, the garage (row 7).
- 6. No PO number twice: pass: MKR-02402401/012, /027, /041, each once. No EPOs.
- 7. Every PO line and measured item matches a price list item: pass: all 6 PO lines and all 7 measured items matched an active row. No warning.
- Vendor: every PO is to Sample Painting Co., V00999.

## Sam's yes
- Answer: yes
- Name: Sam
- Date: 2026-10-17
