# 04 review: Sam decides

## What this stage is for
Sam decides what goes on the request to the builder. The AI lays it out; Sam makes every call.

## What comes in
The highest-numbered `../03 compare/<house>/variance-N.md`. For a re-ask after `06 outcome`, the
outcome Sam answered from and the variance it traces back to.

## What Sam sees
Every row shows its Row number (the read-back row, copied from the variance) and its PO number,
grouped by PO. The Row number is how the script tells apart one item on several lines of one PO.
- **Flagged rows.** These go on the request unless Sam takes one off. If he takes one off, he
  gives a few words on why.
- **Sam's-call rows.** He says chase or leave for each. If he says nothing, write `off` for the row
  ("off (Sam did not choose it)"); never leave the cell blank.
- **Credits back to the builder,** shown as minus rows. Each one is Sam's call, like the rows
  above. A credit is left off unless he says to include it.
- **A flagged credit has no default.** A row that is both flagged and a credit is always a
  question Sam answers, on or off; neither rule above decides it for him. (Jeff, 2026-10-27.)
- **A row whose difference comes only from a back charge has no default.** When Sam's count and
  the rate match the PO and the variance is the back charge taken off the PO amount, putting the row
  on asks the builder to reverse the back charge. Say so in plain words, and Sam answers on or off.
  (Found by the 62 Messy Bay test house, 2026-11-02.)
- **If the house total is flagged:** every ignore row as well, so he sees the small ones together.

**How a decision is written.** The decision cell is exactly `on` or `off`, alone or followed by a
remark in brackets: `off (Sam: leave the doors off)`. A blank cell, or anything else ("on hold",
"only if", "maybe"), is refused by the request script: it means Sam has not decided, so ask him.
  They stay off the request unless he names them, like any row he did not choose.
- **Not-comparable rows,** for his information only. They have no call.

## How Sam answers
One table for the house. He replies yes to accept it as shown, or names the rows he wants to
change. The AI updates the table and shows it again until he says yes. Only a plain yes closes
this stage. "I don't know" leaves it open; it is not a yes to the rows as shown.

## Rows Sam sees but does not decide
Rows compare set apart (not comparable, or left unpriced by Sam) have no decision. List them under
the table as "For information", one line each with the PO, the line and why; they never go on the
request.

## Work on no PO: which EPO it goes on
A row on no PO goes on the request in its own "No PO" group unless Sam names a PO for it in the
"EPO goes on" column. Then it prints inside that PO's group, on its own line with PO qty 0, and
that PO's EPO total includes it. Some builders put every extra on the main PO, the one that carries
the whole list of work (some do: Jeff, 2026-11-08). If `../reference/contractor.md` has a standing
answer under "Work on no PO goes on" for this builder, fill the column from it and write "EPO goes on: standing
answer, contractor.md" in the reason column (the reason column also holds notes like this); Sam sees it in the table he says yes to. Otherwise ask Sam
which PO; never pick it for him. Only a row on no PO can be named onto a PO, and only a PO in this house, written exactly as it
appears under "POs read" (a typo such as an extra digit is refused, never guessed at).

## What goes out
`<house>/review-N.md`, copied from `../templates/review.md`, holding the variance file it came from, each row with Sam's decision, the reason for any flagged row he took
off, his yes, his name and the date. Each review makes one request. The request stage
(`../05 request/`) works from that file.

**Closing the review.** Write Sam's yes, name and date in the review, then run
`python "02 read/seal.py" "04 review/<house>/review-N.md"`. Never set `status: approved` by hand.

**When nothing is on.** If every row matches, or Sam leaves every row off, there is no request.
Sam's yes to the review still closes it: write "nothing to ask for" above the table, his yes, name
and date, then seal it. The house stops here; `05 request` and `06 outcome` do nothing for it.

## What must never happen here
The AI never makes a call for Sam and never fills in a decision he did not give. A row Sam did
not choose never goes on the request.
