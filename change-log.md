# Change log

## 2026-10-27, the money gate (from a 7-agent test round)

A test round on the public kit (a cohort critic, a skeptical contractor, a program judge, an
attacker, a claims checker, a setup walker and a cold job walk) found that the request script
trusted what the AI wrote: a 1-byte file was numbered as a request, a "fail" worded slightly
differently was missed, and every dollar was typed by the AI and checked only by the AI. Fixed:

- `05 request/money.py` (new) works out what the request must say from Sam's approved read-back
  and review only, and checks the variance against them (rates, quantities, EPOs, measured
  quantities in Sam's notes). Records that are unapproved or disagree stop the build.
- `05 request/verify.py` (new) runs all six checks on the PDF itself. Commit runs them again on the
  real file and no longer reads any check the AI wrote; it refuses a non-PDF, a wrong dollar, a
  row Sam left off, a missing PO or EPO, notes he did not agree to, and a request already numbered.
- Build asks for Sam's notes answer (`--notes yes|no`); his site notes go to the builder only if
  he says yes. A file saved twice is attached once; any other file is named, never silently sent.
- `05 request/printing.py` (split out): Chrome before Edge (Edge hung in testing), browsers found
  by name on Linux, Python 3.9 supported.
- `04 review`: a row that is both flagged and a credit has no default; Sam always decides.
- `02 read`: a PO saved twice is read once on Sam's word, and his answer is written down.
- `tests/`: 16 cases: 13 planted mistakes that must be refused, 2 clean cases that must pass, and
  records saved as UTF-16 or with a BOM that must still be read.
- Tester material moved to `_for-testers/`; `AGENTS.md` points other agents to `CLAUDE.md`.

Newest first. What changed, why, and where the idea came from.

## 2026-10-17 (later), first full run, and what it found

Sam approved `reference/contractor.md` (relayed by Jeff, 2026-10-17). A fresh AI then ran
77-mockup-drive through 01 to 05 with only the folder and Sam's yes at each stop. Result matched the
answer key: total variance +$1,008.00; doors +$300 and garage +$672 flagged, stringers +$36
ignored; request $972.00 before tax, $48.60 GST, $1,020.60 total; 1-page request, 5 pages with
proof; `sent: no` (nothing was sent). Output: `read-back-1`, `variance-1`, `review-1`,
`vpo-request-1.pdf`, `request-check-1`. Nothing in `01 intake` changed.
What it found, and the fixes:
- **Bug (mine):** the request-check form's own instruction text contained `fail:`, and the script
  refused any file containing `fail:`, so a faithful copy of the form could never be numbered. The
  run had to rewrite the form to get past it. Fixed: the script now counts findings only on
  numbered check lines, and the form's instructions no longer use the finding words with a colon.
  Tested: a faithful copy commits; a real fail is refused.
- **Gap:** commit did not notice a request check older than the build. Fixed: it now refuses one.
- **Gap:** at review, ignore rows shown because the house total is flagged had no default. Now: off
  unless Sam names them.
- **Gap:** the request's Prepared date, document number and tax label had no source. Now stated in
  `05 request` ("Filling in the header").
- **Gap:** Sam's yes is written into the numbered request check after commit. Now stated as the one
  allowed edit to a numbered file.
- **Open, Sam's to answer later:** the run chose single family and floor area for "3020 sf" from the
  PO's community and showed it under "At risk", which Sam's plain yes accepted. If Sam means
  something else for some houses, that becomes a setup question.

## 2026-10-17, from a cohort partner's run of this folder

A cohort partner ran the folder through to `05 request`. The PDF footer slipped onto a second page while the
request said "page 1 of 1", none of the five checks caught it, and the bad print had already used
request number 1. His notes: (a backup kept outside this repo) (outside this folder).
His three fixes, all made:
1. **Draft first, number only what passes.** The request is printed and checked in
   `05 request/drafts/<house>/`. Only a request with no failed check is copied in as the next
   number. A bad print leaves no trace in the record.
2. **The page count comes from the print.** The layout says "page 1 of {{PAGES}}". The script prints,
   counts, writes the count, and prints again. New check 6: the printed count equals the actual
   pages, and the footer is on the last page.
3. **The build is a script in the folder, not in a session.** New `05 request/build_request.py`
   (Python, PyMuPDF, Edge or Chrome): `build` prints, counts, merges the proof and runs checks 5
   and 6; `commit` numbers the draft only if every check passed, all six are there, and the draft
   did not change after its build.
Also:
- The layout now bounds the parts that vary: "why" is one short sentence, $0.00 tax lines are left
  off (a cohort partner's run printed two PST $0 lines), and the last group and footer stay together.
- The layout's sample numbers now match the answer key (garage $1.60 / $672, total $1,020.60), and
  `request-layout-sample.pdf` was reprinted from it by the script.
- Map, walk test (check 14) and the request-check form updated.
Tested on a copy of the folder, 2026-10-17: a clean build (1 page, 5 pages with proof); a request
made 3 pages long (printed "page 1 of 3", footer on page 3); commit refused on a fail line, on a
missing check, on a missing check file, on a draft edited after its build, and after a failed build;
two good commits numbered 1 then 2; a layout with no {{PAGES}} refused. Two bugs found and fixed in
testing: a hung browser print crashed the script (now retried up to 3 times, then a plain message),
and commit numbered an old draft after a failed build (build now clears old drafts first, and
commit checks the draft is newer than the HTML).
Backup before these changes: (a backup kept outside this repo).

## 2026-10-16 (later), fixes from a second cold walk test

A second cold pass found 16 smaller seams. Fixed:
- `price-list.md` contradicted itself on when to read the CSV. Now: read the CSV for now, with or
  without a connector, until the three rows are in Airtable. Airtable row count corrected to 50.
- The price list date is recorded once at the top everywhere (price-list.md and walk test matched).
- The request layout sample prices the garage at the old $1.25. `05 request` now says the sample is
  layout only, and every name and number comes from the variance.
- `05 request` may read `house-info.md` and the PO headers for the house details on the request.
- `06 outcome` reads every request marked sent, not just the highest. The ledger defines Date and
  Result and has an "earlier outcome" column. Walk test 12 now matches one line per outcome.
- Status: Sam's written yes flips `draft` to `approved`. `attempt:` is the N in the file name.
- The exceptions to "read the stage before" are listed in one place in `CONTEXT.md`.
- A re-ask in `04 review` starts from the outcome. "One request per house" changed to "each review
  makes one request".
- Forms: read-back gained the house details, full PO and EPO headers, measurement notes and an extra
  items list. Outcome gained EPO arrival date, earlier outcome, and a whole-request result. The
  request check has a place for Sam's decision on a `cannot check` line. `contractor.md` has a
  date and a place for Sam's yes.
Left as is, on purpose: `01 intake` still writes no file of its own; `03 compare` still runs on
practice stand-in thresholds, labelled as such; a few facts said in two places (variance meaning,
one contractor per folder) where both say the same thing.

## 2026-10-16 (later), fixes from a cold walk test

A fresh AI walked the folder cold after the changes above and found 21 seams, most of them made
today. Fixed:
- Stages run 01 to 05, then 06 (map said 01 to 05). Two exceptions to "reads only the stage before"
  named (05 attaches intake originals, 06 reads its own EPO drop).
- Thresholds have one home, `contractor.md`. `03 compare` and the map point to it instead of
  repeating the numbers.
- "Where Sam is asked" now lists every stage that asks him (00, 01 on a failed check, 02, 04, 05, 06).
- Numbering: each stage numbers its own files in order and names its source in `from:`. Removed
  "numbered to match", which collided on re-runs. `request-check-N` and `outcome-N` added to the list.
- `03 compare` measured value uses the rate recorded in the read-back, not "from the price list".
- Read-back form: price list date once at the top (02 rule changed to match), EPO "item it pays for"
  column, a table for Sam's answer to each warning item and each "pick one".
- `variance` and `request-check` forms no longer carry a status nothing could change.
- `05 request`: Sam's yes to send, and `sent: yes`, go in the request check. A `cannot check`
  decision is written on its line. `06 outcome` reads the request marked sent.
- A new ask goes back through `04 review`, then `05 request`.
- Ledger: one line per outcome file, after Sam's yes; a sent request with no answer gets a
  "no answer yet" outcome when asked.
- EPOs: before the request they go in `01 intake`; in answer to a request, in `06 outcome`.
- One contractor per folder; a second contractor is a second copy.
- `contractor.md` was marked approved with nobody's yes. Now `draft`, marked as practice stand-ins
  that compare may use and must say so.
- `price-list.md` said the three new rows were in Airtable. They are only in the CSV; fixed.
- Named that step 8 (build the invoice) has no stage yet.
- Every stage contract 02 to 06 now names its form in `templates/`.
Not changed: the change log points to (a backup kept outside this repo) outside this folder on purpose (backups and
the answer key stay out of the AI's reach).
Backup before these fixes: (a backup kept outside this repo).

## 2026-10-16 (later), output forms

New `templates/` with a blank form for each output: `read-back.md`, `variance.md`, `review.md`,
`request-check.md`, `outcome.md`. Each carries the frontmatter (house, attempt, stage, status, the
file it came from) and the tables the stage rules ask for. The map and the walk test (check 13)
point to them. The request PDF already has its own layout in `reference/`.
Why: without forms, each run invented its own layout from the stage prose, so two houses' files
could look different. A cohort partner's `_templates/` do this for briefs, bibles and sidecars.

## 2026-10-16 (later), at risk for this house

`02 read` now lists, above the table, each known trap that applies to this house (wrong unit,
handrail vs railing, floor area vs painted area, quantity and selection disagreeing) with the rows
it touches and what was done.
Why: A cohort partner's spec has an "At risk" table tying each risk for the shot to the exact words that
guard it. Sam's eye should go to the risky rows first, not read 7 rows equally.

## 2026-10-16 (later), three words for a check

`05 request` check lines now use only `pass`, `fail: ...; expected: ...` or `cannot check: why`,
each with its evidence. "Close enough" is not a finding, and `cannot check` is not a pass.
Why: A cohort partner's drift checklist uses `holds`, `drifted` and `cannot see` the same way, so a check
can't quietly pass something nobody actually looked at.

## 2026-10-16 (later), what each document is evidence for

Added a table to `02 read/CONTEXT.md`: what each document (PO, EPO, site notes, price list) may and
may not be used for, and the rule that Sam's notes are matched without looking at the POs.
Why: A cohort partner gives every reference image a "use only for / do not transfer" slip. And the rule "do
not use the POs to decide what a note means" came out of the old kit's tests on Oct 11, but was lost
when PO Verifier was rebuilt.

## 2026-10-16 (later), check the request, and record the outcome

1. **The request is checked before Sam sees it.** `05 request` now reads the finished PDF back and
   runs five checks (only approved rows, differences match the variance, tax per PO, totals add,
   proof attached). Result in `request-check-N.md`. A failed check stops the stage.
   Why: A cohort partner's render audits the image after it is made. The PDF is the only thing the builder
   sees, and nothing checked it.
2. **New `06 outcome` stage and `ledger.md`.** Each EPO the builder issues is matched to the
   request rows it pays: paid in full, in part, refused, or no answer yet. One line per request in
   the ledger: asked, received, difference. Sam confirms the match. Asking again is his call.
   Why: A cohort partner's line ends by filing the image and adding a line to a manifest. Mine ended when Sam
   sent the request, so it could never show dollars recovered, which is the number I need to sell
   the second contractor.
Also: `CLAUDE.md`, the map and the walk test (checks 11 and 12) updated to match.

## 2026-10-16, ideas taken from a cohort partner's character-world-engine

Backup of the folder before these changes: (a backup kept outside this repo) (outside this
folder). Numbers in the answer key are not affected.

1. **Only a plain yes counts.** Added "What counts as Sam's yes" to `CONTEXT.md`, and a line to
   `02 read` and `04 review`. "I don't know" or silence leaves a stage open. His yes, name and date
   go into the file before the next stage reads it.
   Why: the dry run on Oct 15 could not tell what "I don't know" did at review. A cohort partner's folder never
   infers approval from "ok" or "saved".
2. **Rates are frozen at read.** `02 read` now records item, unit, rate and the price list date on
   each row. `03 compare` uses those rates and no longer re-reads the price list. `price-list.md`
   changed from "read it again on every run" to "read it fresh at 02 read".
   Why: a rate changed between Sam's yes and the compare would give him dollars he never confirmed.
   a cohort partner's render refuses to run if an approved input changed.
3. **Nothing is overwritten.** Outputs are numbered: `read-back-N.md`, `variance-N.md`,
   `review-N.md`, `vpo-request-N.pdf`. Later stages read the highest number. Added "Nothing is
   overwritten" to `CONTEXT.md`.
   Why: with a builder, the history is the proof of what was asked for and when. A cohort partner keeps every
   attempt.
4. **A setup stage per contractor.** New `00 setup/CONTEXT.md` (one question at a time) and
   `reference/contractor.md` (stand-in answers for this build). `03 compare` reads its thresholds
   from `contractor.md`. `CLAUDE.md` names the new stage.
   Why: "same core for every contractor, conform at the edges" needs somewhere to keep the edges.
   a cohort partner's `00_setup` interviews once and the rest reads it.
5. **A written walk test.** New `reference/walk-test.md`, 10 yes/no checks for a cold run.
   Why: A cohort partner's `_reference/walk-test.md`. This folder had no test of itself.

Also: the map in `CONTEXT.md` now lists every file, including `price-list.csv`, the request layout
files, `contractor.md`, `walk-test.md`, `00 setup/` and this log. Lesson from the Lena round: the AI
only opens files the map names.

## 2026-10-15, house and price list made to match

- PO MKR-02402401/027 repriced to Summit rates (paint $2.75, railing $38, stringers $9). Originals
  in (a backup kept outside this repo) (outside this folder).
- `reference/price-list.csv` exported from the Summit demo base, plus three rows: wall prime $1,000,
  touch-up $500, 8' doors and trim $60. The three rows are not yet in Airtable.
- Answer key in (a backup kept outside this repo), outside this folder.
Why: the dry run found the house was priced from the old stand-in list, so every rate differed and
three items had no row.
