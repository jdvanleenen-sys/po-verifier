# Phone app: one house, start to finish, from an iPhone

Design approved by Jeff, 2026-11-13. Status (2026-11-18): built in `app/`, ready for testing on an
iPhone. Where the build differs from the first design, this spec now says what was built and why.

## Done, in one sentence
On the laptop that holds the folder, someone on an iPhone in the same room takes a house from its
POs and a notes photo to an approved, checked request PDF on the phone, with no step outside the
app, and the money matches a run of the folder by hand to the cent.

Known limits, outside the app in this version: an item on no price list row is added in Excel on
the laptop, then Sam taps "I added it to my price list" and the read picks it up; and three cases
stop with "call for help" (the laptop's owner): questions still open after three rounds, a request
check that is not "pass" (such as "cannot check"), and a folder refusal the screen cannot fix.
Whether the Done sentence is met is proven by the tests in "Proof of done" 2 to 4, on an iPhone;
the files alone cannot show it.

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
   page covers several houses, he ticks "The notes page shows other houses too"; the address he
   typed names which house this is. Date measured (today by default, or "Not recorded"). One
   button: Lock these files and read them. If the POs print another job address, it asks "Are
   these the POs for <address>?" before anything is locked.
3. **Reading.** Elapsed time, and how long it usually takes. (The headless read reports nothing
   until it ends, so there are no named steps to show.)
4. **Check a couple things.** One card per open question: what was read, why it is asked, and his
   notes photos (tap to zoom); notes sent as a PDF or text file are not shown on screen. Right or
   Fix it, or the choice the card needs. Below, collapsed: every line read. One button, "That's
   all right", is his yes on the read-back.
5. **The difference.** Only the rows that differ, money per row, On the PDF or Leave off per row,
   a preview total before tax, and the attach-my-notes question (asked in words when the page
   covers other houses). Build the PDF records his picks and his yes on the review.
6. **Your PDF.** The request page, the six checks as passes, Approve.
7. **Done.** Save or share the PDF, and "I sent it". Nothing is sent by the app.

Known limit: Safari opens the share sheet only on a secure (HTTPS) page. Over plain Wi-Fi, step 7
may be "download, then share from Files". Tested on a real iPhone before done.

### Kinds of question on screen 4 (found reading `02 read`, 2026-11-13)
Not every open question is a number. Each kind gets its own card:
- **A number:** Right, or Fix it with his number.
- **Pick one:** a line fits two price list items; he taps one.
- **Not on the price list:** he names an existing item, says leave it unpriced, or adds it to his
  price list in Excel on the laptop and taps "I added it to my price list" (sent as `add row`).
- **Anything else the read asks him,** including an "ask Sam:" it wrote outside a table: he answers
  in his own words.
The same file uploaded twice (PO or notes) is refused at Lock, and a file already in another house
is refused there too, so the same file twice is caught before the read. The same PO saved in two
formats (a PDF and a saved page) is not the same file: the read's own check 6 stops on it, and in
this version that is a "call for help" stop, not a card. The one exception is a house
whose read stopped before writing a read-back: starting again with clearer files may reuse its
files, and the old house is marked replaced and can no longer be read. His fixes go into a new numbered read-back with its own grid, as the stage requires, so the read
can take more than one round. After three rounds with questions still open, the house stops with
"Call for help".

### Calls with no default on screen 5 (from `04 review`)
A flagged credit, a row whose count and rate match the PO (its difference is only a back charge or
other EPO already in the PO amount), and a flagged row on no PO with no standing answer for which
PO it goes on all start unset, and Build the PDF stays off until he answers each and the notes
question. Rows he does not touch keep 04 review's default: a flagged row on, any other row
`off (Sam did not choose it)`. When he puts no row on, the screen asks in a few words why, and
every row is written `off (Sam: <his words>)`, as 04 review asks.

### Screen 6
Approve shows only when all six check lines say pass. A `cannot check` line, or any other, stops
before Approve with the check lines shown and "Build it again"; deciding a `cannot check` line on
the phone is not in this version (call for help).

**Moved, 2026-11-14:** the attach-my-notes switch is on screen 5, beside Build the PDF, not on
screen 6. The request prints a proof line naming the notes, and check 5 reads it, so his answer
must be known before the layout is filled. Changing it afterwards means building again.

Approve runs the folder's commit and writes his yes to send. `sent:` stays blank until he taps
"I sent it" on screen 7.

## On a computer (added 2026-11-13, after the phone)
The same page in a laptop or office browser: the same seven steps, taps and order. Wider layout
only: houses in a sidebar with the steps under the open house; files dragged in as well as picked;
the whole notes page beside the question cards with the doubted lines marked; the request PDF at
page size beside the checks and Approve. Planned for after the phone test; built 2026-11-14,
ahead of it, on Jeff's "finish everything". In this version the computer must be on the laptop's
Wi-Fi, and the doubted lines are not marked on the photo.

## One house through the runner
1. **Lock.** Files go into `01 intake/<house>/` and are never changed after: POs as uploaded (a PO
   photo wrapped in a one-page PDF, image unchanged, because the request attaches POs only as PDF
   or page); notes renamed `site-notes`, contents unchanged, because the request knows notes by
   that word. `house-info.md` is written from his answers by code. Houses are named `real-N`.
2. **Read.** Claude Code runs headless in the folder ("read house real-N") and follows `02 read`.
   It stops at the read-back draft. The runner reads the open questions from the read-back's
   tables and grid (plus any "ask Sam:" line outside them), and runs `grid.py check --final` itself.
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
| A PO it cannot read | The reader's reason in plain words; Read again, or Start a new house with clearer files | Nothing reaches compare. Intake is never edited; the clearer copy starts a new house folder (`real-N`), and the stopped house stays as the record |
| A number it doubts | A card on screen 4 | An "ask Sam" cell; the house waits for his answer |
| An answer round or a read stops | "Your last answers did not go through" (or "The read stopped"), the reason, and the cards from the last read-back written | The agent may have written the next read-back before it stopped; the cards come from whichever is highest, and that counts as a round |
| A seal or check refuses | "Stopped before the money: <the folder's reason>", Back to houses; if it does not make sense, call for help (the laptop's owner) | Not sealed, so no number is used up |
| The agent runs long | Elapsed time; past a set limit, Keep waiting or Stop | The runner stops the run; the house stays at its last good step |
| Laptop or Wi-Fi drops | On reopen, the house resumes at its last finished step | State is read from the folder's files, never held only in memory |
| A tap twice | Nothing happens twice | Each step checks the files first; a request number is given once |

Never: fill a gap with a guess. A missing date, lot or number is a question to Sam, or "not
recorded" when he says so.

## Proof of done
1. Tests in the repo: the runner takes 77 Mockup Drive to a PDF matching its sealed answer key;
   failure paths for a read that stops (the stand-in for an unreadable PO: the app sees only the
   reader's STOPPED line), a refused seal, a double Approve, and a restart mid-house.
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
| Nov 19 | Desktop layout, only if the phone passed Nov 17-18 (as planned; built Nov 14 instead, see "On a computer") |
| By Nov 20 | The painter runs the third house |

If the headless read is unreliable on Nov 14, say so that day and switch the read to approach B.

## Not in this version
A link that works away from the laptop, email-in, reminders, square-footage checks, invoicing.
