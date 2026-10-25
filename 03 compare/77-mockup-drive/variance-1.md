---
house: 77-mockup-drive
attempt: 1
stage: 03 compare
from: 02 read/77-mockup-drive/read-back-1.md
price list read: 2026-10-17, from reference/price-list.csv (as recorded in read-back-1)
---

# 77-mockup-drive, variance 1

Copy to `03 compare/<house>/variance-N.md`. Rates come from the read-back named above.

## Rows
| PO number | Item | Unit | Agreed rate | PO qty | PO rate | PO amount | Measured qty | Measured value | Variance | Why | Call |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MKR-02402401/012 | Wall prime, flat rate | EA | $1,000.00 | 1 | $1,000.00 | $1,000.00 | 1 | $1,000.00 | $0.00 | matches | matches |
| MKR-02402401/027 | Basic SF Painting, prime and 2 coat, SINGLE FAMILY | Floor SF | $2.75 | 3020 | $2.75 | $8,305.00 | 3020 | $8,305.00 | $0.00 | matches | matches |
| MKR-02402401/027 | 8' doors and trim | EA | $60.00 | 7 | $60.00 | $420.00 | 12 | $720.00 | +$300.00 | PO quantity short | flag |
| MKR-02402401/027 | Railing, wood | LF | $38.00 | 22 | $38.00 | $836.00 | 22 | $836.00 | $0.00 | matches | matches |
| MKR-02402401/027 | Stringer, inside or outside | LF | $9.00 | 30 | $9.00 | $270.00 | 34 | $306.00 | +$36.00 | PO quantity short | ignore |
| MKR-02402401/041 | Interior paint touch-up, flat rate | EA | $500.00 | 1 | $500.00 | $500.00 | 1 | $500.00 | $0.00 | matches | matches |
| none | Prime and paint garage, including ceiling | SF | $1.60 | 0 | | $0.00 | 420 | $672.00 | +$672.00 | missing from every PO | flag |

No EPOs in the read-back, so no PO amount includes an EPO.

## Not comparable, or left unpriced by Sam
| PO number | Item | Why |
|---|---|---|
| none | | Every row was comparable and priced. |

## Thresholds used
From `reference/contractor.md` (approved, or practice stand-ins: say which): the file is marked
`status: approved` with Sam's yes of 2026-10-17, and its note says the answers are practice
stand-ins. Ignore under $50; Sam's call $50 to under $100; flag $100 and up; house flagged when its
total variance is $100 or more, plus or minus.

## Totals, before tax
- Total of POs: $11,331.00 (1000.00 + 8305.00 + 420.00 + 836.00 + 270.00 + 500.00 + 0)
- Total measured value: $12,339.00 (1000 + 8305 + 720 + 836 + 306 + 500 + 672)
- Total variance: +$1,008.00 (12339.00 - 11331.00; equals the sum of the row variances)
- House flagged on total: yes ($1,008.00 is at or over $100). Sam sees the ignore row together with the rest in review.

## Checks run
Run by a script (`compare.py`, in the session's scratch space; Decimal arithmetic), 2026-10-17.
- Read-back carries Sam's yes, name and date, status approved: pass: "yes", Sam, 2026-10-17.
- Every row has a price list item and rate: pass: 7 of 7; none marked "not on the price list".
- PO amount = PO qty x PO rate, recomputed and equal to the read-back line total: pass: 1000.00, 8305.00, 420.00, 836.00, 270.00, 500.00.
- Measured value = measured qty x agreed rate from the read-back: pass: 1x1000, 3020x2.75, 12x60, 22x38, 34x9, 1x500, 420x1.6.
- Variance = measured value - PO amount: pass: 0, 0, +300, 0, +36, 0, +672.
- Totals: pass: 12339.00 - 11331.00 = 1008.00 = sum of row variances.
- Calls against the thresholds: pass: $300 and $672 at or over $100 (flag); $36 under $50 (ignore); four rows exactly $0 (matches).
- Price list not re-read in this stage: pass: rates taken from read-back-1 only.
