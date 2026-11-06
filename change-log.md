# Change log

## 2026-11-05, cold runs on three PO styles; a checklist PDF was taken for a PO
`tests/po-styles/make_styles.py` prints each style's PO in its builder's own layout, and
`tests/cold_run.py` sets up and scores those houses. Three fresh agents ran Tamarack (French, m2,
GST and QST), Kestrel (legacy ERP, CR credit, spaces in the PO number) and the peer tester's
Birchwood: all three PASS 6 of 6, every figure on the key. Birchwood found a real hole: a painter's
checklist sent as a PDF was taken for a PO, attached whatever Sam answered, and recorded as
"notes: no" though he said yes. A PDF named as notes or a checklist is now his notes, attached only
on his yes, with its file name on every page so no page of it passes for a PO's (check 5). Eight
more findings are recorded, not yet fixed, in `tests/po-styles/results-2026-11-05.md`. 184 tests.

## 2026-11-05, twelve builders' PO styles, and two tax bugs they found
`tests/po-styles/` holds twelve made-up builders, one per style a painter meets (Hyphen-style,
Procore schedule of values, Buildertrend with markup, CoConstruct lump sum, JD Edwards extra PO,
a combined two-PO print, a Quebec PO with GST and QST, a tax-inclusive PO, a QuickBooks PO, a
legacy ERP PO with CR credits, an Excel template with a holdback, and the peer tester's PO).
`tests/test_po_styles.py` runs each through stages 02 to 05 with the stages' own code and plants
mistakes on each. Before the fixes below, 4 of the 12 failed. What they found:
- A correct request was refused when a PO's tax was rounded to the cent: the gate took the rate as
  tax over subtotal (12.99994% for a printed 13%), and check 3 compares the printed rate. The gate
  now takes each tax line's printed percentage, where every line prints one and it gives the
  amount printed; otherwise tax over subtotal, as before.
- A PO with two taxes (GST and QST) was worked out at one combined rate, rounded once; the PO rounds
  each tax on its own. $60.00 came to $8.98 tax instead of $8.99. Each tax is now rounded on its own.
- A PO number with a space (`KBH/2026/0091 Rev 02`) had its first part taken for a PO of its own
  (a bug in the change below, the same day). Fixed.
A tax-inclusive PO is refused at the grid (tax-total), not guessed. 181 tests (was 172). The 13
agent-made requests from 2026-11-04: the same 11 pass.

## 2026-11-05, a second builder's PO: PO numbers and rows read from the read-back
A peer tester ran a made-up second builder (PO SRH-2026-0417, HST 13%, numbered lines 1.01 to 7.02,
walls on four lines of one PO). It passed 01 to 04, and the money gate refused it with 37 problems,
for two reasons, both confirmed in the code:
- The gate knew one builder's PO number shape (`MKR-02402401/027`). A PO number is now taken from
  the read-back's own "POs read" table, as written, spaces included (`OP 4471203`). The request
  check finds a PO group by the house's own PO numbers, and still refuses a group under any
  PO-shaped number the records do not give, or a group with no PO heading at all.
- A row was named by PO and item, so one item on four lines of one PO was refused. The variance
  (written by `compare.py`) and the review now carry a Row column, the read-back row number, and the
  gate matches on it. A variance or review without it (written before today) still works where PO
  and item name one row, and is refused where they do not. On the request, an item on more than one
  approved row of one PO prints with the PO's own line number: `Walls, PO line 3.01`.
Also: the header check refused nothing when a PO gave no "JOB NAME:" and house-info gave no
address or lot; it now refuses. `money.py` was split (pure moves, checked by comparing every
definition): `records.py` reads the tables. 172 tests (was 156); 12 of the 16 new ones fail on the
code before this change, the other 4 are controls. The 13 agent-made requests from 2026-11-04:
the same 11 pass.

## 2026-11-05, test loop on the request checks: 13 holes found and closed
A build-test loop (8 cycles, every probe's expected result written down before it ran) attacked the
six PDF checks after the peer-test fix below. Each hole was reproduced first, then fixed with a test
that failed before the fix. Every fix was also run against the 13 numbered requests that agents made
in the 2026-11-04 cold runs: the same 11 pass before and after (the other 2 fail for reasons recorded
on 11-04), so no fix refuses a request an agent drafted correctly. What now gets refused:
- A row the records do not give: an extra row, an approved row printed twice, a block for a PO with
  no approved row, or a row printed without a sign (check 2).
- A wrong PO qty or measured qty on a row; a malformed amount such as `$1,02,0.60` (check 2).
- Any dollar amount no record gives, anywhere on the request: an invented figure in a why or a
  box note (check 1). The box note's per-PO totals must be each PO's own (check 4).
- A group whose last line is worded for the wrong kind: money owed worded as a credit, a credit
  worded as an EPO request, the no-PO group worded as a PO's EPO (check 3).
- A tax rate on a group's tax line that is not that PO's own; an item count in the before-tax box
  that is not the number of approved rows (checks 3, 4).
- A PO missing from the proof whose number appears only on its EPO's page (check 5; reproduced on a
  real build of 40 Larch Crescent with its PO 027 file removed).
- A header with the wrong job name, lot, house number or date measured, or a document number that is
  not the number the commit gives (check 6; a request numbered 3 used to pass printing VR-0001).
No longer wrongly refused: a left-off item whose name sits inside an approved one ("8' doors" inside
"8' doors and trim"), and a why that names a later row's item with a price.
`verify.py` was split (pure moves, checked by comparing every definition before and after):
`request_text.py` reads the PDF text, `row_checks.py` reads each row, `header_checks.py` reads the
header. 156 tests (was 117). Not covered: the "Prepared" date, the vendor number, a PO job name on
a builder's PO that does not use the words "JOB NAME:", and a notes file long enough to run onto a
second page with a PO number written there.

## 2026-11-05, each row's figures are read from that row (peer-test finding)
A peer's test agent found that check 2 accepted a row's difference if the right amount appeared
anywhere on the request. A row printed +$999.00 passed, because the right +$220.00 sat on the
subtotal line under it. Reproduced here on 77 Mockup Drive (+$300.00 changed to +$999.00, every
money check passed), then fixed:
- Check 2 reads each approved row inside its own PO's block: the first signed amount after the
  item's name is its difference, and the plain amounts before it are the agreed rate, PO amount and
  measured value. All four must equal the figures `money.py` works out from Sam's read-back. A name
  inside a longer name, the same item on two POs, a row under the wrong PO and a PO heading printed
  twice are each handled.
- Check 3 also checks each group's "Difference before tax"; a wrong subtotal used to pass.
- `money.py` hands verify each row's rate, PO amount and measured value, not only the difference.
- The layout rules and `05 request/CONTEXT.md` say so: only the difference carries a sign; a no-PO
  row prints its PO amount as $0.00.
- `tests/test_row_binding.py`: 12 tests. 11 fail on the old checks; all pass now (117 in all).
  The full build on 77 Mockup Drive passes; with the planted +$999.00 the commit refuses (exit 1).
Not covered: quantities (PO qty, measured qty) are not checked on the row, only the dollar
figures; a row whose PO amount is printed without an EPO already paid will now be refused.

## 2026-11-04, the break-it loop: 3 rounds, 15 cold runs, 2 sealed houses
Ten new attack houses and two sealed ones (written by a separate agent, opened only in round 3).
Money matched the key on all 15 runs; every run made its PDF from round 2 on. Full record, PDFs and
the honest close: `C:/GitHub/po-verifier-runs/2026-11-04_loop/results.md` (outside this folder).
esults.md` (outside this folder).
- Checks 3 and 4 read each labelled line with its sign. A credit printed as money owed used to pass.
- Photo and voice-memo notes attach; Sam can name only some pages; check 5 refuses a page he left out.
- The rule grid asks Sam, by code, about a dot-for-comma number, a tenfold miss, a 0 against a PO
  line, and the same line on two POs, until the row says "Sam confirmed".
- A credit request is labelled "Total credit to the builder"; the layout fixes the proof-line and
  credit-group wording; a group's heading is its first PO.
- 00 setup asks how he writes measurements and what a per-SF rate counts. Stand-ins in contractor.md.
- Tester copies leave out README.md.
Not fixed: agents read an `ls` header as a line of the notes (asked Sam, never priced); "page 1 of 1"
with proof after it; no phone front end.

## 2026-11-03, three messy-input test houses

- **Added:** `14-photo-notes-close` (one handwritten photo, a crossed-out count, work on no PO),
  `27-voice-memo-way` (a phone voice-memo transcript) and `36-two-photos-lane` (two photos, one
  sideways, glare over a number). `tests/houses/handwriting.py` draws the photos from the text in
  `houses.json`, so the key always matches the page. `make_houses.py` writes photo, voice or typed
  notes; `test_houses.py` checks the key against the notes' text.
- **Cold runs:** two PASS, one FAIL on the request step. Every money figure matched. The runs used a
  copy from before the rule grid, so they still need a run on this branch. Results and open
  findings in `tests/houses/results-2026-11-03.md`.
- **Not fixed yet:** `05 request/build_request.py` cannot attach photo or voice notes.
Why: a real painter sends phone photos of handwritten notes, and maybe voice memos, not typed notes.

## 2026-11-02 (evening), the rule grid: every row checked against every rule, one cell each

Jeff's ask: verify each line item against one rule at a time, to get rid of silent errors. The checks
were a list the AI wrote ("pass: 7 of 7"), so a row that was never checked looked the same as one
that passed.

- **New: the rule grid.** `02 read/grid.py build <house>` writes `grid-N.md` beside `read-back-N.md`,
  with one cell per row per rule (10 rules) and per PO per PO rule (5 rules). Code fills every cell
  it can work out; the AI answers the rest one rule (one column) at a time. `grid.py check` refuses a
  blank or `?` cell, a missing or extra row, a changed code cell, a `fail`, an at-risk row not named
  under its trap in At risk, and a read-back changed after its grid was built. `--final` also
  refuses `ask Sam`. Rules in `grid_rules.py`; reading in `grid_read.py`; checking in `grid_check.py`.
- **New: `03 compare/compare.py` writes the variance by code.** It replaces a `compare.py` that each
  run wrote in its own scratch space. It refuses a read-back without Sam's yes or a grid that fails
  `--final`. Its arithmetic (`compare_rows.py`) is kept apart from the money gate on purpose.
- **"Not comparable" is now marked in `02 read`**, in the grid's `count` column, so Sam sees it in the
  table he says yes to. Before, compare marked it and the money gate demanded the row anyway.
- **The money gate refuses a request with no grid or a grid that fails `--final`**, and no longer
  demands a variance row for a row the grid marks not comparable.
- **Fixed: a back charge against another trade was counted against Sam in the money gate.** 02 read
  says it still pays Sam. Found when `compare.py`, written apart from the gate, disagreed with it. The
  gate refused the house rather than pass it.
- **Found by the grid in the test data:** the unpriced-row test added a $210 line to PO /027 without
  changing its printed subtotal. The old checks never looked. The fixture is now an extra item on no PO.
- **77 Mockup Drive** gets `02 read/77-mockup-drive/grid-1.md`, built 2026-11-02 after its read-back
  was approved on 2026-10-17. Its code cells agree with the checks written then; its 23 judgment
  cells were answered on 2026-11-02, one rule at a time. Its read-back and variance are unchanged;
  `compare.py` gives the same variance to the cent.
- A Python cache file that was committed before `.gitignore` listed it is no longer tracked.
- Tests: 38 to 77 (grid 24, compare 12, gate 3 more, one fixture fixed).

Not done: the six test houses have not been cold-run on the new grid yet, and an at-risk check only
knows the three traps code can see (unit, selection, notes).

## 2026-11-02 (later), what the six cold runs found, fixed

Six fresh agents each ran one test house from `tests/houses/` cold, with Jeff's session playing Sam.
- **Fixed: a row Sam left unpriced could not pass the money gate honestly.** `03 compare` lists
  unpriced rows separately with no dollars, but `money.py` demanded every read-back row in the
  variance table, so the only way through was a fake credit for the row's whole PO amount. The run
  on 30 Not Listed Road refused to write one and stopped. The gate now skips rows marked "not on the
  price list", and refuses one that shows up in the variance Rows table with dollars.
- **Fixed: a row waiting on Sam's "pick one" failed the 02 read price check**, so the table could
  never pass before he saw it. `prices.py check` now passes it and says how many wait on him; the
  money gate still refuses any.
- Tests: 2 cases for unpriced rows and 1 for pick-one rows (they fail on the old gate).

## 2026-11-02, the price list is one file, and code checks every rate

Jeff's call: run the prices from one price list that anyone testing has, with no database login.

- `reference/price-list.csv` is now the price list, not a copy of Airtable. Sam keeps it in Excel
  and saves it as "CSV UTF-8 (Comma delimited)". `reference/price-list.md` rewritten to match.
- `02 read/prices.py` (new). `snapshot <house>` checks the file (four columns, a number in every
  rate, a known unit, no item active twice, a clear message for a semicolon file) and freezes an
  unchanged copy as `02 read/<house>/price-list-N.csv`, with its sha256 written into the
  read-back's `price list read:` line. `check <house>` refuses any read-back row whose item, unit
  or rate differs from that snapshot, or names an inactive item.
- The money gate (`05 request/money.py`) runs the same check, so no request is numbered from a
  rate that is not on the frozen list, or from a snapshot edited after the read.
- `tests/test_price_list.py`: 18 cases (9 on the file Sam saves from Excel, 8 on the read-back's
  rates). With the check switched off, 7 of the gate tests fail, so they test it.
- 77 Mockup Drive: `02 read/77-mockup-drive/price-list-1.csv` saved 2026-11-02 from the same
  price list it was read from on 2026-10-17 (the file has not changed since 2026-10-15), and its
  read-back's `price list read:` line now names it. No rate or number changed.
Why: the rates were read by the AI's eyes and checked by nobody. A wrong rate gives Sam a wrong
dollar on a request he signs.

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

Round 2 (a cold run on the fixed code, 2026-10-27) matched the sealed key to the cent and found 2
more: the read-back form let items on no PO sit only in a bullet list the gate cannot verify (now
they are table rows with PO `none`), and when the gate refused, the agent edited 2 files Sam had
approved instead of renumbering them. The refusal now says how to fix it the right way (next
number, Sam's yes again), the review form says to copy item names exactly, and the limit is
declared in `_for-testers/TESTING.md`.

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
