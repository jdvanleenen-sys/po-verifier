# Phone app: one house, start to finish, from an iPhone

Design approved by Jeff, 2026-11-13. Status: spec, not built.

## Done, in one sentence
On the laptop that holds the folder, someone on an iPhone in the same room takes a house from its
POs and a notes photo to an approved, checked request PDF on the phone, with no step outside the
app, and the money matches a run of the folder by hand to the cent.

## Why
The folder works, but it runs in a chat. Sam works from his truck. He should put the POs and his
notes in, check the few numbers the folder doubts, pick what to chase, approve, and get the PDF,
without seeing a chat, a file name or a command.

## Decided
- First use: a demo with a real painter by 2026-11-20, sitting beside the person who runs the
  laptop. Same room, same Wi-Fi. A link that works from anywhere comes later.
- Phone: iPhone, in Safari. No App Store.
- Screens: the flow of the v2 phone mockup (2026-11-10), wired to real work.
- How POs reach the phone is not known yet. The app accepts all three: a file (PDF or saved page),
  a photo or screenshot, and (later) a forwarded email.
- Approach A: the folder does the work, unchanged; a small runner drives it. Approach B (call the
  Claude API directly for the read) is the fallback only if the headless read proves unreliable.
  Approach C (screens in front of a person running a chat) was rejected: staged, not real.

## The parts
| Part | Job | Where |
|---|---|---|
| Phone screens | The 7 screens below. Show what the folder says; collect Sam's taps | One web page served to Safari |
| Runner | Take the uploads, run each step in order, know where each house is | A small Python server (Flask) on the laptop, in `app/` |
| The folder | Do the job under its own rules | The contractor's private copy of this folder. Unchanged |

The runner is told the folder's path when it starts. Houses live only in that folder. Nothing in
`app/` holds a real PO, name, address or rate.

## The screens
1. **Houses.** Each house with its status, and a New house button.
2. **New house.** Address (typed). Add POs (Files, Photos or camera). Add notes photo. When one
   page covers several houses: "Which house on this page?" Date measured (today by default, or
   "Not recorded"). One button: Lock these files and read them.
3. **Reading.** Named steps with elapsed time. Says plainly that it takes minutes.
4. **Check a couple things.** Only the grid's "ask Sam" cells, one card each: what was read, the
   line from his notes, the photo (tap to zoom), Right or Fix it. Below, collapsed: the lines read
   cleanly. One button, "That's all right", is his yes on the read-back.
5. **The difference.** Only the rows that differ, money per row, a switch per row, total before
   tax. Build the PDF records his picks and his yes on the review.
6. **Your PDF.** The request page, the six checks as passes, the attach-my-notes switch (asks in
   words when the page covers other houses), Approve.
7. **Done.** Save or share the PDF. Nothing is sent by the app.

Known limit: Safari opens the share sheet only on a secure (HTTPS) page. Over plain Wi-Fi, step 7
may be "download, then share from Files". Tested on a real iPhone before done.

### Kinds of question on screen 4 (found reading `02 read`, 2026-11-13)
Not every open question is a number. Each kind gets its own card:
- **A number:** Right, or Fix it with his number.
- **Pick one:** a line fits two price list items; he taps one.
- **Not on the price list:** he names an existing item or says leave it unpriced. Adding a row means
  editing the price list in Excel: in this version the card says so and the house waits.
- **Same PO twice:** he says whether it is one PO saved twice.
His fixes go into a new numbered read-back with its own grid, as the stage requires, so the read
can take more than one round. After three rounds with questions still open, the house stops with
"Call for help".

### Calls with no default on screen 5 (from `04 review`)
A flagged credit, a row whose difference is only a back charge, and a row on no PO with no
standing answer for which PO it goes on all start unset, and Build the PDF stays off until he
answers each. Rows he does not touch are written `off (Sam did not choose it)`.

### Screen 6
A `cannot check` line from the request's checks is his call, shown as a card above Approve.

## On a computer (added 2026-11-13, after the phone)
The same page in a laptop or office browser: the same seven steps, taps and order. Wider layout
only: houses in a sidebar with the steps under the open house; files dragged in as well as picked;
the whole notes page beside the question cards with the doubted lines marked; the request PDF at
page size beside the checks and Approve. Built on Nov 19 only if the phone is solid; otherwise
after Nov 20. In this version the computer must be on the laptop's Wi-Fi.

## One house through the runner
1. **Lock.** Files go into `01 intake/<house>/` untouched; `house-info.md` is written from his
   answers by code. Houses are named `real-N`.
2. **Read.** Claude Code runs headless in the folder ("read house real-N") and follows `02 read`.
   It stops at the read-back draft. The runner gets the open questions from `grid.py check`.
3. **His answers.** His fixes go back to the agent, which writes the next numbered read-back and
   grid. When `grid.py check --final` passes and he taps That's all right, the runner writes his
   yes in the folder's format (his words, name, date) and runs `seal.py`.
4. **Compare.** `compare.py`. No AI.
5. **Review.** The runner writes his picks and his yes into `04 review`, then `seal.py`.
6. **Request.** The agent fills the request layout (the stage's one drafting step), then
   `build_request.py build` runs the six checks. Approve runs `commit`, which gives the number.

Rules: AI only reads and fills layout; every dollar comes from the scripts. Every yes is a tap by
Sam, written with his name and the date, then sealed; the runner never says yes for him. The
headless agent uses the laptop's own Claude login; no API key.

## When something goes wrong
| What | Sam sees | Underneath |
|---|---|---|
| A PO it cannot read | "I couldn't read PO 2 of 3. Add a clearer copy or a PDF." | Nothing reaches compare. Intake is never edited; a re-add starts `<house>-2` |
| A number it doubts | A card on screen 4 | An "ask Sam" cell; the house waits for his answer |
| A seal or check refuses | "Stopped before the money: <the folder's reason>", Fix it or Call for help | Not sealed, so no number is used up |
| The agent runs long | Elapsed time; past a set limit, Keep waiting or Stop | The runner stops the run; the house stays at its last good step |
| Laptop or Wi-Fi drops | On reopen, the house resumes at its last finished step | State is read from the folder's files, never held only in memory |
| A tap twice | Nothing happens twice | Each step checks the files first; a request number is given once |

Never: fill a gap with a guess. A missing date, lot or number is a question to Sam, or "not
recorded" when he says so.

## Proof of done
1. Tests in the repo: the runner takes 77 Mockup Drive to a PDF matching its sealed answer key;
   failure paths for an unreadable PO, a refused seal, a double Approve, and a restart mid-house.
   The existing suite still passes.
2. Two routes, same cents: a real house through the app on an iPhone, and the same house by hand in
   a fresh chat. Variance and request match exactly.
3. A cold run on a second real house by the laptop's owner on an iPhone, timed, with every
   hesitation written down.
4. A third real house is kept unrun for the painter to run live. The held-out house stays held out.

## Schedule (estimates)
| Day | What |
|---|---|
| Nov 14 | Measure the headless read on a real house; the runner and its tests |
| Nov 15-16 | The 7 screens, wired to the runner |
| Nov 17 | First iPhone runs; the share-sheet test |
| Nov 18 | Cold run on a second house; fixes |
| Nov 19 | Final run-through; buffer |
| Nov 19 | Desktop layout, only if the phone passed Nov 17-18 |
| By Nov 20 | The painter runs the third house |

If the headless read is unreliable on Nov 14, say so that day and switch the read to approach B.

## Not in this version
A link that works away from the laptop, email-in, reminders, square-footage checks, invoicing.
