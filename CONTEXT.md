# PO Verifier: the map

## What this is
It checks a builder's POs against what the trade measured on site, and builds the request for the
difference. This is a practice build. The data is made up and nothing is ever sent.

## What is here

| Folder or file | What it holds |
|---|---|
| `CLAUDE.md`, `the-page.md` | Where to start, and who this is for and why |
| `reference/price-list.md` | Where the price list lives and how to read it |
| `reference/price-list.xlsx` | The price list, the only one. Sam keeps it in Excel; the checker reads its "Price list" sheet |
| `02 read/grid.py` | The rule grid: every read-back row and PO against every rule, one cell each. Code fills what it can; the AI answers the rest one rule at a time. Its helpers: `grid_rules.py` (the rules), `grid_read.py`, `grid_check.py` |
| `02 read/seal.py` | Seals a record once Sam's plain yes is written: the only way a record becomes approved. Writes the house's own `seals.md` ledger beside the record (one per house per stage). `chain.py` checks each record's number, `attempt:` and `from:` |
| `03 compare/compare.py` | Writes the variance by code from the approved read-back and its grid. Its arithmetic is `compare_rows.py`, kept apart from the money gate |
| `02 read/contractor.py`, `02 read/intake_read.py` | Who the folder is for (read from `reference/contractor.md`; a PO to another vendor is refused), and the fingerprint of every intake file, written into each grid and checked before a request is built or numbered |
| `02 read/prices.py` | Reads the Excel price list (through `price_excel.py`), checks it, freezes a copy per read-back (`price-list-N.csv`), and checks every rate in the read-back against it |
| `reference/contractor.md` | Who the contractor is and his settings, written by `00 setup` |
| `reference/walk-test.md` | The checklist for testing this folder cold |
| `reference/request-layout.html`, `request-layout-sample.pdf` | How the request looks |
| `00 setup/` | Run once per contractor. Writes `reference/contractor.md` |
| `01 intake/` | What arrives for each house, untouched |
| `02 read/` | The documents turned into rows, confirmed by Sam |
| `03 compare/` | The difference, worked out by calculation |
| `04 review/` | Sam's decisions |
| `05 request/` | The request for the site super, checked before Sam sees it |
| `05 request/build_request.py` | Prints the request, merges the proof, runs the six checks on the PDF, and numbers only a request that passed. Its helpers: `money.py` (works out what the request must say from Sam's approved records, reading them with `records.py`), `house_checks.py` (the contractor, intake, draft-PDF and one-request-per-review checks), `verify.py` (the six checks, reading the PDF text with `request_text.py`, each row with `row_checks.py`, the header with `header_checks.py`), `printing.py` (the browser) |
| `tests/` (left out of a tester's copy) | Planted mistakes the money gate, the price check and the rule grid must refuse, and the variance code checked against the gate: `python -m unittest discover -s tests` |
| `tests/houses/` | Six test houses with POs, site notes, Sam's answers and the key; `tests/cold_run.py` runs one cold and scores it. For testing the folder, not for the agent doing the job |
| `05 request/drafts/` | The workbench for a request before it passes. Not the record |
| `06 outcome/` | What the builder paid against each request |
| `06 outcome/ledger.md` | One line per request: asked, received, the difference |
| `templates/` | Blank forms for each stage's output: read-back, variance, review, request check, outcome |
| `change-log.md` | What changed in this folder, when and why |
| `README.md`, `_for-testers/` | For people testing the folder, not for the agent doing the job |

Each stage folder has a `CONTEXT.md` that says what happens there. Read it before working in it.
Each stage writes its output by copying its form from `templates/`, so every house's files look alike.
`00 setup` writes straight into `reference/contractor.md`, which is its own form. `01 intake` writes
nothing; its checks pass or it asks Sam.

## How a house moves through
A house goes through the stages in order, 01 to 05, then 06 when the builder answers. In every
stage it has its own folder, named for its address, such as `77-mockup-drive`. A stage only starts
when the one before it has finished. The original documents stay in `01 intake` and are never moved
or copied. Each later stage reads what the stage before it wrote, and writes only its own output
into its own house folder. Two exceptions: `05 request` also attaches the originals from
`01 intake` as proof, and `06 outcome` reads the EPOs Sam drops into its own house folder.

**Where an EPO goes.** An EPO the builder issued before the request (part of what the house was
priced at) goes in `01 intake`. An EPO issued in answer to a request goes in `06 outcome`.

**One contractor per folder.** `reference/contractor.md` is this folder's contractor. A second
contractor is a second copy of the folder, set up through `00 setup`.

## How things are named
- **Sam:** the contractor this folder is set up for, whoever `reference/contractor.md` names. In a
  real contractor's copy, read "Sam" as that person; the yes is always his.
- **PO number:** the ORDER # printed on a PO. It is the job number, a slash, and a running number.
  It goes on every row and is never dropped.
- **EPO and VPO:** two names for the same document. EPO is an extra purchase order; VPO is a
  variance purchase order. It has a total and no lines, and names the PO it belongs to. Sam asks
  for one; the site super writes it in the builder's system.

## What the numbers mean
- Variance is measured value minus PO amount. A plus is money owed to Sam. A minus is a credit
  back to the builder.
- The thresholds for the calls live in `reference/contractor.md`, and only there. How they are
  applied, and the house-total rule, are in `03 compare/CONTEXT.md`.
- Tax is taken from each PO's own figures. See `05 request/CONTEXT.md`.

## What lives somewhere else
- The POs come from the builder's ordering system (SupplyPro). The files here are copies.
- EPOs are written and approved in the builder's system, not here.

## Where Sam is asked
- `00 setup`: once, to answer the setup questions and approve `contractor.md`.
- `01 intake`: only if a check fails (something is missing).
- `02 read`: to confirm what was read, and to answer each price-list warning.
- `04 review`: to decide what to chase.
- `05 request`: to approve the request he will send, and to decide any `cannot check` line.
- `06 outcome`: to confirm which EPO pays which request row.
`03 compare` runs without him.

## What counts as Sam's yes
Only a plain yes to the whole table. "I don't know", a question, a partial answer or silence
leaves the stage open, and the next stage does not start. An "I don't know" about one row leaves
that row open: its grid cell says `ask Sam:`, and the stage cannot close until he answers it.
His yes, his name and the date are written into the "Sam's yes" block of the stage's output file.
The Answer is "yes" alone, or exactly "yes, to the whole table", "yes, to the table exactly as
shown" or "yes, to the table with those decisions" (any case, a full stop allowed). Anything else,
such as "Yes?", "Yes, but take row 7 off", "Yes and no" or "yes-ish", is not a yes: a condition or a
question means the table changes first, and seal.py refuses it. Then, and only then, run
`python "02 read/seal.py" <file>`. It refuses anything that is not a plain yes, sets `status:
approved`, and seals the file: from then on every script refuses the file if a single character of
it changes, or if it is copied under another number. seal.py also writes a line in the folder's
`seals.md` ledger (for a read-back, with the sha256 of its grid), and refuses a file already in the
ledger: an approved file is sealed once, never edited and sealed again. Every script refuses an
approved file that is in no ledger line, whose seal is not the ledger's, or whose grid changed after
the yes. Never edit `seals.md`. **Never set `status: approved` by hand**, and
never seal a file Sam did not answer. A yes said in chat but not written to the file does not count.
A correction to an approved file is a new numbered file with its own yes, never an edit.
seal.py also refuses a record that another record already names in its `from:` or `from review:`
line (a read-back's own grid does not count), and a record that leaves a numbering gap below it:
a record something was built from is never approved after the fact. Before sealing, seal.py runs
what the next stage would check, so a refused record never uses up a number: the record's
`attempt:` (required, equal to its file number), its `from:` (required, naming an existing record of
this house), no gap below it, and, for a read-back, `grid.py check <house> --final` (only the highest
read-back is sealed). For a review, it also runs what the request build would refuse
(`05 request/review_gate.py`): its `from:` names a variance of this house, every decision is exactly
on or off, every row's PO and item are exactly in that variance, every "EPO goes on" is a PO of this
house and follows the standing answer. The Date under Sam's yes is written as YYYY-MM-DD, such as
2026-11-09; anything else is refused, and on a review it must be a real day not after today. What the seal does not
do: the ledger guards against mistakes, not against someone deleting its lines on purpose. The real
guard is Sam giving his yes from his own screen, so no one else can write it for him.

## Nothing is overwritten
Every house output is numbered: `read-back-N.md`, `variance-N.md`, `review-N.md`,
`vpo-request-N.pdf`, `request-check-N.md`, `outcome-N.md`. Each stage numbers its own files 1, 2, 3
in the order it writes them (`attempt:` in the file is that same N), and each file names the file
it was made from in its `from:` line. A
correction or a re-run writes the next number and keeps the old one. Until Sam's yes is written,
a file is a draft and may be updated in place; once it is approved, it is never edited again. A later stage reads the
highest number in the stage before it, with three exceptions: `05 request` uses the variance the
review names, `06 outcome` reads each request marked sent, and a re-ask in `04 review` starts from
the outcome Sam answered. The old files are the record of what was asked for and
when. (`reference/contractor.md` is not numbered; it is the folder's settings, changed only through
`00 setup`.)

## What this folder does not do yet
Step 8 on `the-page.md`, building the invoice on the checked totals, has no stage yet.

## What must never happen
- Nothing in `01 intake` is ever changed.
- No dollar amount is written by judgment. Every one comes from a calculation.
- No check counts as passed unless its cell in the rule grid says so.
- The AI never makes a call for Sam and never sends anything.
- If something is unclear, stop and ask Sam. Never guess.
