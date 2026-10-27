# 05 request: build the VPO request

## What this stage is for
Turn Sam's approved rows into one request for the house, with the proof attached. Sam sends it to
the builder's site super, who writes the EPO.

## What comes in
- The highest-numbered `../04 review/<house>/review-N.md`, with Sam's yes.
- The `../03 compare/<house>/variance-N.md` that review names, for the numbers.
- The original POs, EPOs and measurements in `../01 intake/<house>/`, as proof, and
  `house-info.md` and the PO headers there for the house details (address, lot, builder,
  community, job name, date measured).

## What the request holds
- **The house:** address, lot, builder, community, job name.
- **The rows, grouped by PO number.** The site super writes one EPO per PO, so each PO gets its
  own group, headed by its PO number. Each row shows the item, the PO quantity and amount, Sam's measured quantity and
  value, the difference, and why.
- **Tax on every group.** For each PO group: the difference before tax, each tax line, and the
  total. Use the tax lines and rates printed on that PO, worked out from its own subtotal and tax
  amounts. Never assume a rate. Every request carries tax, because every sale has tax. The
  "no PO" group uses the rate on the house's other POs. If those POs carry different rates, stop
  and ask Sam.
- **Items on no PO** go in their own group, marked "no PO", so the site super knows a new PO
  or EPO is needed.
- **Credits** Sam chose to include, shown as minus rows inside their PO group.
- **The total for the house:** before tax, the tax, and the total.
- **The proof:** a list of every document attached.

## How it looks
Follow `../reference/request-layout.html` for layout only. Its sample numbers match the answer
for 77 Mockup Drive, but never copy them: every name and number comes from the variance and the
review. A printed sample is `../reference/request-layout-sample.pdf`. The rules in the comment at
the top of the layout apply: leave `{{PAGES}}` as it is, keep each "why" to one short sentence,
leave off any $0.00 tax line and say so in the tax note, and keep the last group and the footer
together. Show only the rows Sam approved. Matches, ignored rows
and rows Sam left off are not on the request.

## How the sums are done
Every difference is copied from the compare, never worked out again. The tax and the totals come
from a calculation, run and shown. The script then works them all out again on its own, from Sam's
approved read-back and review, and refuses a request where any figure differs (`money.py`).

Write each row's item exactly as the variance names it (the price list's name), and print every
difference with its sign and a dollar sign (`+$300.00`, `-$170.00`): the script finds them that way.

## Filling in the header
- **Prepared:** the date the request is built.
- **Document:** `VR-` and the request number this commit will give, four digits (the next free
  number in `<house>/`, so `VR-0001` for a house's first request).
- **Tax:** name each tax as the PO prints it (for example "GST/HST 5%").

## Ask Sam one thing before the build
"Attach your site notes to the request as proof?" His notes are his own scribbles, so they go to
the builder only if he says yes. Write his answer into the proof list on the request.

## How the PDF is made: draft first, number only what passes
The PDF is never written straight into the record. A print that goes wrong must cost nothing.
1. Copy the layout to `drafts/<house>/request.html` and fill it in from the review and variance.
2. Run `python "05 request/build_request.py" build <house> --notes yes` (or `--notes no`, Sam's
   answer) from the folder root. Before printing, it checks that Sam's read-back and review are
   approved and that the variance agrees with them; then it prints the request with "page 1 of N"
   from the real count, attaches each PO and EPO once (a file saved twice goes once), adds the
   notes only if Sam said yes, and names any other file it did not attach. Then it runs all six
   checks below on the PDF itself and writes them to `drafts/<house>/script-checks.md`. If one
   fails, fix the draft and build again.
3. Only when all six pass, run `python "05 request/build_request.py" commit <house>`. It runs the
   six checks again on the draft PDF, trusting nothing written about it, and only then copies it
   in as the next numbered `vpo-request-N.pdf` and writes `request-check-N.md`. It refuses a file
   that is not the built request, a request already numbered, or a draft changed after its build.
If the build says Sam's records do not agree, never edit a file he approved to make it pass: write
the corrected record as the next number, show it to Sam, and get his yes again.
`drafts/` is a workbench, not the record. Anything in it may be deleted.
The script needs Python 3.9 or newer with PyMuPDF, and Chrome, Chromium or Edge. Prove it on your
machine with `python -m unittest discover -s tests` from the folder root.

## The six checks (the script runs them; nobody writes them by hand)
1. Every row on it is a row Sam approved in the review, and no row he left off is on it.
2. Each row's difference equals the figure worked out from Sam's read-back.
3. Each PO group's tax uses that PO's own printed rate, and the group adds up.
4. The house total before tax, the tax and the total add up from the groups.
5. Every PO and EPO in the read-back is attached, and the notes only if Sam said so.
6. The page count printed on the request equals its actual pages, and the footer is on the last
   page.

Each line reads `pass: <evidence>` or `fail: <what is on the PDF, and what was expected>`. If any
check fails, nothing is numbered and Sam does not see the request.

## What goes out
`<house>/vpo-request-N.pdf` and `<house>/request-check-N.md`, numbered by the script's commit,
for Sam to check. Sam reads both and says yes to the request he will send. His yes, his name, the
date, and `sent: yes` go in the yes block the script left blank in the request check. This yes block is the only part of a numbered request check written after the
commit; nothing else in a numbered file changes. A changed request is the next number; a request already sent is never replaced. Sam
sends it to the site super himself.

## What must never happen here
Only rows Sam approved go on the request. The AI never sends it, and never contacts the builder
or the site super.
