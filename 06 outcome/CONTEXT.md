# 06 outcome: what the builder paid

## What this stage is for
A request is not the end. This stage records what the builder actually issued against it, so
every house ends as a number: asked for, received, and the difference.

## What comes in
- Each EPO the builder issued after the request, dropped by Sam into `<house>/` in this folder,
  untouched, with the date it arrived.
- The request it answers: each `../05 request/<house>/vpo-request-N.pdf` whose request check says
  `sent: yes`, and its rows. Sam says which request an EPO answers if it is not clear.

## What is worked out
Match each EPO to the request rows it pays, by PO number, account code and notes, the same way
`02 read` matches an EPO. For each request row: asked, received, and the difference. Each row is
one of: paid in full, paid in part, refused, or no answer yet. Every number comes from a
calculation, run and shown.

## How Sam confirms
He sees one table: each request row, the EPO matched to it, and the result. Only a plain yes
closes it (see "What counts as Sam's yes" in `../CONTEXT.md`). Whether to ask again for a row paid
in part or refused is Sam's call. A new ask goes back through `04 review`: a new review with the
rows he wants to ask for again and his yes, then a new request in `05 request`.

## What goes out
- `<house>/outcome-N.md`, copied from `../templates/outcome.md`, numbered in the order written.
  It names the request it answers, any earlier outcome for that request, and carries Sam's yes,
  his name and the date.
- After Sam's yes, one line added to `ledger.md` in this folder: one line per outcome file. Lines
  are only added, never changed. A later answer to the same request is a new outcome and a new
  line that names the earlier one. A request sent with no answer yet gets an outcome of
  "no answer yet" when Sam asks for one, so no sent request is missing from the ledger.

## What must never happen here
The AI never contacts the builder or the site super. It never marks a row paid without an EPO in
the folder. It never edits an EPO.
