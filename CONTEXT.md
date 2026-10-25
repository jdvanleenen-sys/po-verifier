# PO Verifier: the map

## What this is
It checks a builder's POs against what the trade measured on site, and builds the request for the
difference. This is a practice build. The data is made up and nothing is ever sent.

## What is here

| Folder or file | What it holds |
|---|---|
| `CLAUDE.md`, `the-page.md` | Where to start, and who this is for and why |
| `reference/price-list.md` | Where the price list lives and how to read it |
| `reference/price-list.csv` | The price list to read for now (Airtable lacks three rows) |
| `reference/contractor.md` | Who the contractor is and his settings, written by `00 setup` |
| `reference/walk-test.md` | The checklist for testing this folder cold |
| `reference/request-layout.html`, `request-layout-sample.pdf` | How the request looks |
| `00 setup/` | Run once per contractor. Writes `reference/contractor.md` |
| `01 intake/` | What arrives for each house, untouched |
| `02 read/` | The documents turned into rows, confirmed by Sam |
| `03 compare/` | The difference, worked out by calculation |
| `04 review/` | Sam's decisions |
| `05 request/` | The request for the site super, checked before Sam sees it |
| `05 request/build_request.py` | Prints the request, counts its pages, merges the proof, checks it, and numbers only a request that passed |
| `05 request/drafts/` | The workbench for a request before it passes. Not the record |
| `06 outcome/` | What the builder paid against each request |
| `06 outcome/ledger.md` | One line per request: asked, received, the difference |
| `templates/` | Blank forms for each stage's output: read-back, variance, review, request check, outcome |
| `change-log.md` | What changed in this folder, when and why |

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
- **PO number:** the ORDER # printed on a PO. It is the job number, a slash, and a running number.
  It goes on every row and is never dropped.
- **EPO:** the builder's extra PO. It has a total and no lines, and names the PO it belongs to.
- **VPO:** what Sam asks for. The site super writes it as an EPO.

## What the numbers mean
- Variance is measured value minus PO amount. A plus is money owed to Sam. A minus is a credit
  back to the builder.
- The thresholds for the calls live in `reference/contractor.md`, and only there. How they are
  applied, and the house-total rule, are in `03 compare/CONTEXT.md`.
- Tax is taken from each PO's own figures. See `05 request/CONTEXT.md`.

## What lives somewhere else
- The price list is in Airtable. See `reference/price-list.md`.
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
leaves the stage open, and the next stage does not start. His yes, his name and the date are
written into the stage's output file before the next stage reads it, and the file's `status`
changes from `draft` to `approved`. A yes said in chat but not written to the file does not count.

## Nothing is overwritten
Every house output is numbered: `read-back-N.md`, `variance-N.md`, `review-N.md`,
`vpo-request-N.pdf`, `request-check-N.md`, `outcome-N.md`. Each stage numbers its own files 1, 2, 3
in the order it writes them (`attempt:` in the file is that same N), and each file names the file
it was made from in its `from:` line. A
correction or a re-run writes the next number and keeps the old one. A later stage reads the
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
- The AI never makes a call for Sam and never sends anything.
- If something is unclear, stop and ask Sam. Never guess.
