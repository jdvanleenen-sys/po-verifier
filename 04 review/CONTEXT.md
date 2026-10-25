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

## What must never happen here
The AI never makes a call for Sam and never fills in a decision he did not give. A row Sam did
not choose never goes on the request.
