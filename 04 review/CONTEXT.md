# 04 review: Sam decides

## What this stage is for
Sam decides what goes on the request to the builder. The AI lays it out; Sam makes every call.

## What comes in
The highest-numbered `../03 compare/<house>/variance-N.md`. For a re-ask after `06 outcome`, the
outcome Sam answered from and the variance it traces back to.

## What Sam sees
Every row shows its PO number, grouped by PO.
- **Flagged rows.** These go on the request unless Sam takes one off. If he takes one off, he
  gives a few words on why.
- **Sam's-call rows.** He says chase or leave for each. If he says nothing, the row is left off.
- **Credits back to the builder,** shown as minus rows. Each one is Sam's call, like the rows
  above. A credit is left off unless he says to include it.
- **A flagged credit has no default.** A row that is both flagged and a credit is always a
  question Sam answers, on or off; neither rule above decides it for him. (Jeff, 2026-10-27.)
- **A row whose difference comes only from a back charge has no default.** When Sam's count and
  the rate match the PO and the variance is the back charge taken off the PO amount, putting the row
  on asks the builder to reverse the back charge. Say so in plain words, and Sam answers on or off.
  (Found by the 62 Messy Bay test house, 2026-11-02.)
- **If the house total is flagged:** every ignore row as well, so he sees the small ones together.
  They stay off the request unless he names them, like any row he did not choose.
- **Not-comparable rows,** for his information only. They have no call.

## How Sam answers
One table for the house. He replies yes to accept it as shown, or names the rows he wants to
change. The AI updates the table and shows it again until he says yes. Only a plain yes closes
this stage. "I don't know" leaves it open; it is not a yes to the rows as shown.

## What goes out
`<house>/review-N.md`, copied from `../templates/review.md`, holding the variance file it came from, each row with Sam's decision, the reason for any flagged row he took
off, his yes, his name and the date. Each review makes one request. The request stage
(`../05 request/`) works from that file.

**When nothing is on.** If every row matches, or Sam leaves every row off, there is no request.
Sam's yes to the review still closes it: write "nothing to ask for" above the table, his yes, name
and date. The house stops here; `05 request` and `06 outcome` do nothing for it.

## What must never happen here
The AI never makes a call for Sam and never fills in a decision he did not give. A row Sam did
not choose never goes on the request.
