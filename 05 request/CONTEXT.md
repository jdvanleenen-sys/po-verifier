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
from a calculation, run and shown.

## Filling in the header
- **Prepared:** the date the request is built.
- **Document:** `VR-` and the request number this commit will give, four digits (the next free
  number in `<house>/`, so `VR-0001` for a house's first request).
- **Tax:** name each tax as the PO prints it (for example "GST/HST 5%").

## How the PDF is made: draft first, number only what passes
The PDF is never written straight into the record. A print that goes wrong must cost nothing.
1. Copy the layout to `drafts/<house>/request.html` and fill it in from the review and variance.
2. Run `python "05 request/build_request.py" build <house>` from the folder root. It prints the
   request, counts the pages, writes "page 1 of N" from that count and prints again, merges the
   proof from `01 intake/<house>/`, and checks what a script can check (page count, footer on the
   last page, proof attached). Its findings go in `drafts/<house>/script-checks.md`. If it fails,
   fix the draft (usually a "why" that is too long) and build again.
3. Read the draft PDF back and do the checks below. Write all six lines to
   `drafts/<house>/request-check.md`, copied from `../templates/request-check.md`. Copy checks 5 and
   6 from the script's findings.
4. Only when no line says `fail`, run `python "05 request/build_request.py" commit <house>`. It
   copies the draft in as the next numbered `vpo-request-N.pdf` and `request-check-N.md`. It
   refuses if any line failed, if a check is missing, or if the draft changed after its build.
`drafts/` is a workbench, not the record. Anything in it may be deleted.
The script needs Python 3 with PyMuPDF, and Edge or Chrome.

## Check the request before Sam sees it
The compare can be right and the PDF still wrong, and the PDF is the only thing the builder sees.
Check the draft PDF, with a calculation run and shown:
1. Every row on it is a row Sam approved in the review, and no other row is on it.
2. Each row's difference equals the variance file's figure for that row.
3. Each PO group's tax uses that PO's own printed rate, and the group adds up.
4. The house total before tax, the tax and the total add up from the groups.
5. Every document in the proof list is attached. (From the script.)
6. The page count printed on the request equals its actual pages, and the footer is on the last
   page. (From the script.)

Write one line per check, each with one of three findings and the evidence:
- `pass: <what was checked, with the numbers>`
- `fail: <what is on the PDF>; expected: <what the review or variance says>`
- `cannot check: <why>`. This is not a pass. Sam sees it and decides, and his decision is
  written on that line.
"Close enough" or "looks right" is not a finding. If any check
fails, say which and stop. Sam does not see a request that failed a check.

## What goes out
`<house>/vpo-request-N.pdf` and `<house>/request-check-N.md`, numbered by the script's commit,
for Sam to check. Sam reads both and says yes to the request he will send. His yes, his name, the date, and `sent: yes` go in the
request check. This yes block is the only part of a numbered request check written after the
commit; nothing else in a numbered file changes. A changed request is the next number; a request already sent is never replaced. Sam
sends it to the site super himself.

## What must never happen here
Only rows Sam approved go on the request. The AI never sends it, and never contacts the builder
or the site super.
