# PO styles

Every builder prints a PO its own way. These are twelve made-up builders, one per style a painter
meets, so the folder is tested on more than one builder's PO. Every name, address and number here
is made up. Each style imitates, in spirit only, a system builders use; no real PO was copied.

`styles.json` holds each style: the PO lines, the painter's price list and site counts, the rows
Sam puts on, and what must happen. `pipeline.py` turns a style into the records a correct run
writes (read-back, rule grid, variance, review) using the stages' own code, and works out the
answer key on its own. `tests/test_po_styles.py` runs every style through the money gate and the
request checks, and plants mistakes on each.

| House | Style it imitates | What it tests | Must |
|---|---|---|---|
| `12-quarry-lane` | Hyphen SupplyPro trade PO, "Order" as the quantity column, a not-to-exceed EPO | PO number with a slash, an EPO counted in the PO amount | request: $190.00 + $9.50 |
| `40-larchmont-way` | Procore schedule of values, amount-only lines, 10% retainage | lump sums set apart; work on no PO taxed at the PO's 13% | request: no-PO $720.00 + $93.60 |
| `7-fieldstone-court` | Buildertrend PO with a markup column; a variance PO linked to it | the PO price is the cost plus markup; two POs | request: two groups |
| `3-harrow-pine-road` | CoConstruct PO: inclusions, exclusions, one lump-sum line | a lump sum set apart; numbers in scope text are not counts | request: $45.00 + $2.25 |
| `88-ostrander-drive` | JD Edwards extra PO: cost code, option number, GST and PST (BC) | a PO number with a space (`OP 4471203`); a $0.00 option line; two taxes | request: $105.00 + $12.60 |
| `15-belvoir-bend` | Infor combined print: one document, lines from two POs, GST and PST (SK) | two POs in one PDF; a credit back to the builder | request: one owed, one credit |
| `9-tamarack-rue` | Quebec PO in French and English, decimal commas, m2, GST and QST | square metres set apart; each tax rounded on its own | request: $60.00 + $8.99 |
| `21-glenhollow-lane` | Xero PO with amounts tax inclusive | tax already in the line prices | refused at the grid (tax-total) |
| `5521-prairie-gate` | QuickBooks PO: a bare number, one combined GST/PST 12% line (MB) | walls on four lines of one PO, no line numbers | request: two walls rows, each named by its line |
| `4-kestrel-bay` | Legacy ERP PO (Atlantic): `KBH/2026/0091 Rev 02`, SQ FT, no $ signs, a CR credit line | spaces in a PO number; a credit line set apart; HST 15% | request: $87.50 + $13.13 |
| `118-summit-ash-street` | Excel or Word template: lines 1.1 and 2.1, a discount row, a 10% holdback, no lot | a discount row left unpriced; the holdback is not a price | request: $105.00 + $5.25 |
| `27-birchwood-crescent` | A peer tester's made-up builder (Summit Ridge Homes), 20 numbered lines, HST 13% | walls, ceilings and railings on many lines of one PO | request: walls (PO line 3.01) and railing (PO line 7.02) |

Where the evidence for each style came from (vendor help pages read on 2026-11-05):
- Hyphen SupplyPro and BuildPro order and EPO pages: hyphensolutions.com/MH2SUPPLY/Help and /Build/Help
- Procore commitment numbering and schedule of values: support.procore.com
- Buildertrend variance POs: buildertrend.com/help-article/bills-purchase-orders-on-mobile
- CoConstruct PO parts: coconstruct.com/learn-construction-software/components-of-a-purchase-order
- JD Edwards extra POs: docs.oracle.com (JD Edwards Homebuilder, extra purchase orders)
- Infor CSI combined builder PO print: docs.infor.com/csi
- Xero tax-inclusive amounts; QuickBooks Canada combined GST/PST codes
No full sample PO from any of these systems is public. The layouts are built from their field
names and documented behaviour, so a real PO from a real builder is still the test that counts.

Not supported, and refused rather than guessed: tax-inclusive prices; a PO line in a different unit
system from the price list (it is set apart until Sam gives the conversion).
