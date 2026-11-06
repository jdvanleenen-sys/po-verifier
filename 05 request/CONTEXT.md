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
approved read-back and review, and refuses a request where any figure differs (`money.py`). It
also refuses one whose read-back has no rule grid, or a grid that fails `grid.py check --final`.

Write each row's item exactly as the variance names it (the price list's name). When the same item
is on more than one approved row of one PO (walls on four lines of one PO), print each with the PO's
own line number after a comma, as the PO numbers its lines: `Walls, PO line 3.01`. Where the PO
numbers no lines, follow the comma with the line as printed in the read-back. Print every
difference with its sign and a dollar sign (`+$300.00`, `-$170.00`): the script finds them that way.
Copy each row's agreed rate, PO qty, PO amount and measured qty from the compare too; the measured
value is the measured quantity times the agreed rate. Each quantity is one plain number (`12`,
`2,615.5`): the PO's own count, `0` on a no-PO row, and the PO amount includes any EPO already
issued for the row (say so in the why). A no-PO row prints its PO amount as `$0.00`, never blank. The
script reads every one of these from the row it belongs to.

## Filling in the header
- **Prepared:** the date the request is built.
- **Document:** `VR-` and the request number this commit will give, four digits (the next free
  number in `<house>/`, so `VR-0001` for a house's first request).
- **Tax:** name each tax as the PO prints it (for example "GST/HST 5%").

## Ask Sam one thing before the build
"Attach your site notes to the request as proof?" His notes are his own scribbles, so they go to
the builder only if he says yes. Notes can be typed, a phone photo (.jpg, .png), a voice-memo
transcript, or a checklist PDF, and there can be several pages. The script knows a notes file by a
word in its name: note, checklist, measurement or voice-memo. Any other PDF is taken for a PO or EPO
and always attached. So before the build, if a PDF in intake is Sam's notes but its name has none of
those words, stop and tell Sam it would go to the builder whatever he answers; renaming it is his call.
If there is more than one notes page, ask which: all of them, or only the pages he names. A page that is not for this house is never attached. Write his answer into
the proof list on the request.

## How the PDF is made: draft first, number only what passes
The PDF is never written straight into the record. A print that goes wrong must cost nothing.
1. Copy the layout to `drafts/<house>/request.html` and fill it in from the review and variance.
2. Run `python "05 request/build_request.py" build <house> --notes yes` (or `--notes no`, or
   `--notes only:<file>,<file>` for just the pages he named; Sam's answer) from the folder root. Before printing, it checks that Sam's read-back and review are
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
1. Every row on it is a row Sam approved in the review, and no row he left off is on it. Every
   dollar amount printed is one the records give (a row or group figure, a PO rate, an EPO total);
   an amount nobody can trace back is refused.
2. Each row's agreed rate, PO qty, PO amount, measured qty, measured value and difference, read from that row inside
   its own PO's block, equal the figures worked out from Sam's read-back. A right number printed
   somewhere else on the page does not count.
3. Each PO group's difference before tax, tax and total, read from that group's own lines with
   their sign, match Sam's records, and the rate printed on its tax line is that PO's own. A credit
   must print with its minus sign.
4. The three boxes at the top (before tax, tax, total requested), each read from its own label
   with its sign, match the groups; each per-PO total named in the box note is that PO's own, and
   the item count in the before-tax box is the number of rows Sam approved.
5. Every PO and EPO in the read-back is attached, each notes page Sam named is attached, and no
   page he left out is. A PO counts only from its own page; its number on an EPO or notes page
   does not.
6. The header names the right job (the address and lot numbers in `house-info.md`, and each PO's
   job name, and the date measured in `house-info.md`) and the document number this commit gives (`VR-0002` for a house's second request);
   the page count printed equals the actual pages, and the footer is on the last page.

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
