# Build plan: the phone app

From the spec `docs/specs/2026-11-13-phone-app-design.md`. If this plan and the spec disagree, the
spec's "Done" sentence wins. Status (2026-11-18): steps 0 to 6 and 8 built; ready for testing.
Steps 7 (iPhone over Wi-Fi) and 9 (proof of done on real houses) are the testing.

## Done
The spec's "Done, in one sentence" is the definition; it lives only there.

## Must not break
- Every stage folder, script, rule and template. The app calls them; it never edits them. If a
  script has to change, that is a separate branch with its own tests, not part of this one.
- The 426 tests on main. Run the whole suite before each commit.
- `01 intake/<house>/` is written once, at Lock, and never again.

## Must not do without the laptop's owner
- Install anything (Flask is the one package planned; ask first).
- Run on a real house outside a throwaway copy before step 0 passes.
- Commit a real PO, name, address, rate or photo. Real houses stay `real-N`, gitignored.
- Write a yes Sam did not tap, or send anything anywhere.

## What has to be true but hasn't been checked yet
| What | Checked by | If it is false |
|---|---|---|
| A headless Claude Code run in the folder reads a house and stops cleanly at the draft read-back | Step 0 | Switch the read to approach B (Claude API) |
| A headless run takes minutes, not tens of minutes | Step 0 | Raise the wait limit; say so on screen 3 |
| Every question the read raises is one of the four card kinds in the spec | Steps 0 and 3, on real houses | Add the kind, or "Call for help" for it |
| Safari on the iPhone can upload a PDF, an HTML page and a photo to a plain-HTTP page on the laptop | Step 7 | Fall back to photos only for the demo |
| The share sheet works, or "download, then Files" is acceptable to the painter | Step 7 | Show the PDF full screen to save it |
| The laptop's firewall lets the phone reach the server | Step 7 | One firewall rule, with the owner |

## Parts, in `app/`
Each file under 300 lines, each function under 50. Standard library apart from Flask, plus PyMuPDF
(which the folder's request stage already needs). No build step. The table below is the first plan;
the parts as built, with their jobs, are in `app/README.md`, which is the one current list.

| File | Job |
|---|---|
| `server.py` | The routes only: list houses, new house, upload, status, answer, pick, approve, the PDF |
| `houses.py` | Where each house stands, worked out from the folder's files every time (no state in memory) |
| `steps.py` | Run each step in order: lock, read, answer round, compare, review, request, commit |
| `agent.py` | Start the headless agent for one task and wait for it, with a time limit. The one place approach B would plug in |
| `questions.py` | Turn the grid's `ask Sam` cells and the warning table into cards |
| `records.py` (built as `sam_yes.py`, see improvement 3) | Write his yes and his review picks in the folder's own formats, then call `seal.py` |
| `jobs.py` | One job per house at a time; a second tap while one runs does nothing |
| `static/index.html`, `app.js`, `app.css` | The seven screens. Polls status every few seconds while a step runs |
| `README.md` | How to start it, point it at a folder, and open it on the phone |

The runner is started with the folder's path: `python app/server.py --folder "<path>"`. It refuses
to start on a folder with no `reference/contractor.md`.

## Where a house stands, read off the files
Worked out by `app/houses.py` from the house's files every time, never held in memory. That file's
`stand()` is the one statement of the rule (including the Stopped screen for a record that says
approved but fails its seal); it is not copied here so it cannot drift.

## Build order
Each step ends with its tests passing, the whole suite passing, a commit, and a push to
`feature/phone-app`.

**Step 0. Measure the headless read (Nov 14, morning).** In a throwaway copy of the private folder
(the painter's settings, real-3 from a real house's POs and notes), run the read twice. Record: time, whether it
stopped at the draft, `grid.py check` result, what questions it raised, and anything it did that
the stage forbids. Pass: both runs stop at the draft with a grid built, no forbidden action, each
under 15 minutes. Write the result in the private folder (evidence, phone-app, step 0; not in this
public repo) and the
plain numbers (no real data) in the commit message. Fail means approach B, said that day.

*Result, 2026-11-14: passed on the second prompt.* Four runs on one real house. The first two had
no date measured and POs printing a placeholder job address: one stopped before writing, one wrote a
draft whose grid refused the address. With those two answers given up front, both runs stopped at a
checked draft in 3 min 39 s and 3 min 47 s, about $2 each (API-equivalent), intake unchanged.
Approach A stays. Two changes follow:
- **Lock asks two things before the read:** the date measured (or not recorded), and, when code
  finds the POs' job address does not match the typed one, "Are these the POs for <address>?".
  His answers go into the read prompt; the agent writes them into the read-back.
- **The questions can differ between runs** on the same files (one line was a "not on the price
  list" warning in one run and a "pick one" in another). Both block the money until he answers.
  Proof 2 (same cents by two routes) therefore compares after his answers, not the question lists.

**Step 1. Houses and state.** `houses.py` and its table above. Tests: every row of the table on
77 Mockup Drive copies, plus a folder with no houses.

**Step 2. Lock and read.** `steps.lock` writes intake and `house-info.md` from his answers;
`agent.py` runs the read; `jobs.py` stops a second start. Tests use a stand-in agent that copies
the test house's read-back, so no test calls Claude. Failure tests: an empty upload, a file type
that is not PDF, HTML or an image, a second Lock, the agent running past its limit.

**Step 3. Questions and answer rounds.** `questions.py` for the four card kinds; an answer round
sends his answers to the agent for the next read-back; That's all right writes his yes and seals.
Tests: each card kind from a planted grid; a seal refused by `seal.py` shows the folder's reason
and seals nothing; the three-round stop.

**Step 4. Compare and review.** `compare.py`, then screen 5's rows from the variance, with the
no-default rows unset; his picks written into `review-N.md` and sealed. Tests: picks round-trip to
the file exactly; Build the PDF refused while a no-default row is unset; "nothing to ask for".

**Step 5. Request and approve.** The agent fills the request layout; `build_request.py build`;
the six checks shown; Approve runs `commit` once. Tests: 77 Mockup Drive end to end with the
stand-in agent, request matching its sealed answer key; a double Approve gives one number; a
restart mid-house resumes at the right screen.

**Step 6. The screens.** The seven screens from the design page, wired to the routes. No emojis;
loading and error states on every step. Checked by driving them in a desktop browser at phone width.

**Step 7. On the iPhone (Nov 17).** The laptop's owner opens it in Safari over Wi-Fi. Upload each
file kind, run 77 Mockup Drive through, test save and share. Write down every hesitation.

**Step 8. Desktop layout (Nov 19, only if step 7 passed).** Same page, wider layout, drag and drop.
*Built 2026-11-14 ahead of step 7, on Jeff's "keep going ... finish everything"; it changes only
the layout at 900px and wider, so the phone test is unaffected.*
If step 7 left fixes open, this waits until after Nov 20.

**Step 9. Proof of done (Nov 18-20).** The spec's four proofs: the test suite; one real house
through the app and the same house by hand in a fresh chat, same cents; a timed cold run on a
second real house; the third house kept for the painter. The held-out house stays held out.

## The prompts the agent gets
Three short task prompts, kept in `app/prompts/`, each naming the stage file to follow and where
to stop: read a house, write the next read-back from these answers, fill the request layout. They
give no rules about the work; the stage `CONTEXT.md` files are those rules. Each carries only the
task, Sam's answers, today's date, where to stop, a three-try budget on the stage's own check, and
the one-line ending the app reads (improvement 6). Each is tested in step 0 or the step that first
uses it.

## Improvement log
Each round: one test that tries to break something, what it found, the one change, the proof.
Rungs are Bas Rosario's ladder (1 prompt, 2 context, 3 memory, 4 loop).

| # | Test | Found | Change | Proof |
|---|---|---|---|---|
| 1 | Headless read, prompt v1, twice | Stopped on the date and the address: answers Sam must give before the read (rung 2) | Lock asks both; answers go in the prompt | Runs 3 and 4 reach a checked draft |
| 2 | Live read through the app | A prose `ask Sam:` the final check does not block | Every prose ask is a card; Lock refuses a PO already in another house | 3 questions, 3 cards |
| 3 | Full suite after step 3 | `app/records.py` hid `05 request/records.py`: 33 errors, pushed | Renamed; a test refuses any clash | 470 pass |
| 4 | Review dated 2099 | Sealed: CRLF hid the date from `review_gate.py` | App writes LF everywhere; folder bug logged | Refused, file taken back out |
| 5 | Browser, Difference to Done | Steps bar on the list, "compare" label, "PO none" | CSS `[hidden]`, labels | Clicked through to VR-0001 |
| 6 | Prompts against rung 1 and rung 4 | No retry budget or hand-back on the grid check; no date for Prepared (rung 2) | Three-try budget, fixed target, STOPPED with the failing lines; today's date in the request prompt | 46 app tests pass |
| 7 | Prompt blanks | A missed edit sent `{today}` unfilled | `agent.prompt` refuses any blank left | Caught it on the first run |
| 8 | The app on the real folder, read only | Practice houses listed for the painter | A real folder lists only `real-N` houses | 2 tests |
| 9 | Browser: New house and the Check cards (stand-in raising questions) | Empty left column with no photo; "PO none" | Split only with a photo; "On no PO" | Address question, cards, blank answer refused, missing grid stopped |
| 10 | Live, whole house through the routes, real agent | iPhone names photos `image.jpg`; the request knows notes only by "note" in the name, so the build refused | Lock names notes `site-notes[-N]`; a PO photo is wrapped in a PDF, image unchanged | 2 tests; live rerun |
| 12 | Live rerun, whole house, real agent | Passed: VR-0001, six checks, notes photo attached, PDF read back and its totals match the checks (figures in the private copy). The request build took 9 min 27 s; the screen said 2 to 4 | Waiting text 5 to 10 min; "taking longer" at 15 min | 922 s upload to Approve, about $5.20 of agent time |
| 13 | Ship check (cold reader, 2026-11-18) | HOLD: 24 quote-verified findings. Dead ends (Stopped screen, a stopped read), a failed answer round shown silently, Build the PDF never off, an untouched no-PO row written off, "nothing to ask for" without his words, a "cannot check" line passing as pass, and spec lines left from before the build | Way-out buttons, a failed-answers notice, Build off until answered, his call on a flagged no-PO row, his words when nothing is on, only "pass" passes, same file twice refused at Lock, spec and plan brought in line | Re-frozen and re-checked |
| 14 | Readiness loop for the first iPhone run (9 pass/fail checks, fixed target, budget 3) | The painter's folder would show older hand-run houses with stale drafts and refuse a fresh upload of the same POs; iOS may grey out a saved PO page in a filtered picker | A hide list (`_app/hidden.json`, records untouched); no type filter on the pickers (the server still refuses bad types) | Round 2: all 9 pass except the iPhone itself; dress rehearsal on a copy of the painter's folder, upload to Approve in 7 min 13 s, same cents as the Nov 14 run |
| 11 | Start on the laptop by hand | Setup steps easy to miss | `app/start.ps1`: sets up, checks Claude Code and the folder | Link printed; 403 without key; wrong folder refused |

## Found in the folder while building (fix on their own branch, not this one)
- `05 request/review_gate.py`: the Date regex ends `[ \t]*$`, so a review saved with CRLF line
  endings skips the "not after today" check. The app writes LF; a review typed by hand on Windows
  would not be checked. (2026-11-14)
- The final grid check does not block on an `ask Sam:` the read writes in prose (under Checks run).
  The app shows each one as a card; a run by hand in chat could pass it unseen. (2026-11-14)

- `05 request/build_request.py` knows a notes file only by a word in its name and attaches a PO only
  as PDF or HTML. The app renames notes and wraps PO photos at Lock; a house dropped in by hand
  still meets both. (2026-11-14)

## Open, not the builder's call
- How POs reach the painter's iPhone (asking the painter).
- Who the yes is written as: built as the first `- Name:` line of `contractor.md`, read at each yes.
  Whether that is the right person (the painter, not the office) is the painter's call.
- Whether real numbers can be shown at Demo Day.
