# Build plan: the phone app

From the spec `docs/specs/2026-11-13-phone-app-design.md`. If this plan and the spec disagree, the
spec's "Done" sentence wins. Status: plan, not started.

## Done
On the laptop that holds the folder, someone on an iPhone in the same room takes a house from its
POs and a notes photo to an approved, checked request PDF on the phone, with no step outside the
app, and the money matches a run of the folder by hand to the cent.

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
Each file under 300 lines, each function under 50. Standard library apart from Flask. No build step.

| File | Job |
|---|---|
| `server.py` | The routes only: list houses, new house, upload, status, answer, pick, approve, the PDF |
| `houses.py` | Where each house stands, worked out from the folder's files every time (no state in memory) |
| `steps.py` | Run each step in order: lock, read, answer round, compare, review, request, commit |
| `agent.py` | Start the headless agent for one task and wait for it, with a time limit. The one place approach B would plug in |
| `questions.py` | Turn the grid's `ask Sam` cells and the warning table into cards |
| `records.py` | Write his yes and his review picks in the folder's own formats, then call `seal.py` |
| `jobs.py` | One job per house at a time; a second tap while one runs does nothing |
| `static/index.html`, `app.js`, `app.css` | The seven screens. Polls status every few seconds while a step runs |
| `README.md` | How to start it, point it at a folder, and open it on the phone |

The runner is started with the folder's path: `python app/server.py --folder "<path>"`. It refuses
to start on a folder with no `reference/contractor.md`.

## Where a house stands, read off the files
| Files present | Screen |
|---|---|
| None for this house | 2 New house |
| Intake, no read-back, or a read job running | 3 Reading |
| Highest read-back is a draft | 4 Check |
| Sealed read-back, no variance | compare runs, then 5 |
| Variance, no sealed review | 5 The difference |
| Sealed review, no committed request | 6 Your PDF |
| Committed request | 7 Done |
| Sealed review saying "nothing to ask for" | 7 Done, no PDF |

## Build order
Each step ends with its tests passing, the whole suite passing, a commit, and a push to
`feature/phone-app`.

**Step 0. Measure the headless read (Nov 14, morning).** In a throwaway copy of the private folder
(the painter's settings, real-3 from a real house's POs and notes), run the read twice. Record: time, whether it
stopped at the draft, `grid.py check` result, what questions it raised, and anything it did that
the stage forbids. Pass: both runs stop at the draft with a grid built, no forbidden action, each
under 15 minutes. Write the result in `evidence/phone-app/step-0.md` in the private folder and the
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
If step 7 left fixes open, this waits until after Nov 20.

**Step 9. Proof of done (Nov 18-20).** The spec's four proofs: the test suite; one real house
through the app and the same house by hand in a fresh chat, same cents; a timed cold run on a
second real house; the third house kept for the painter. The held-out house stays held out.

## The prompts the agent gets
Three short task prompts, kept in `app/prompts/`, each naming the stage file to follow and where
to stop: read a house, write the next read-back from these answers, fill the request layout. They
give no rules of their own; the stage `CONTEXT.md` files are the rules. Each is tested in step 0
or the step that first uses it.

## Open, not the builder's call
- How POs reach the painter's iPhone (asking the painter).
- Who the yes is written as: the name in `contractor.md`, set once when the runner starts.
- Whether real numbers can be shown at Demo Day.
