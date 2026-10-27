# Testing the PO Verifier

Thank you for testing. The goal is to find where it breaks, so a finding is worth more than a
pass, and "this is worthless" is a fair answer if you mean it. Plan on 45 to 75 minutes.

Repo: https://github.com/jdvanleenen-sys/po-verifier

## What you need
- **An AI coding agent that works in a folder**, such as Claude Code (it needs a Claude account).
  Claude Code reads `CLAUDE.md` first; other agents read `AGENTS.md`, which points there.
- **Python 3.9 or newer** with PyMuPDF:
  - Windows: `python -m pip install pymupdf`
  - Mac or Linux: `python3 -m pip install pymupdf` (if pip refuses with "externally managed",
    make a virtual environment first: `python3 -m venv .venv` then `source .venv/bin/activate`)
- **Google Chrome** (Chromium or Edge also work) for printing the request to PDF. Chrome is
  recommended: Edge has hung while printing in testing. If yours is somewhere unusual, set
  `BROWSER` to its full path, for example
  `C:\Program Files\Google\Chrome\Application\chrome.exe` or
  `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`.

**Check your setup in 10 seconds.** From the repo folder run
`python -m unittest discover -s tests` (`python3` on Mac or Linux). It plants mistakes the money
gate must refuse. You want to see `OK` at the end.

Work in your own copy of this repo. Nothing in it is real, and nothing gets sent.

## The job
Open the repo folder in your agent and give it this, word for word:

> Sam just dropped in a new house, 14 Example Crescent. Run it through the folder and build the
> request for the difference.

Then let it work. **Give it no other hints**: the test is whether the folder alone gets it there.
`01 intake/77-mockup-drive` is a house that has already been run; leave it as it is.

## You play Sam
Sam is the painter. The agent will stop and ask him things. Answer as Sam, using these answers,
so every tester's run can be compared:

- **If it asks about a PO that appears twice:** "That's the same PO downloaded twice. Read it
  once, and leave both files in intake."
- **When it shows the read-back table:** check it against the POs and the site notes in
  `01 intake/14-example-crescent/`. If it matches, say "Yes, to the whole table." If something is
  wrong, say what, as Sam would.
- **At review:** "Include the French door credit. Chase the 8' doors. Leave the stringers and the
  headers off. Keep the other flagged rows on. Yes, to the table with those decisions."
- **If it asks whether to attach your site notes:** "Yes, attach them."
- **At the end, when it asks if this is the request he will send:** "Yes, but this is practice,
  so it is not being sent. Write sent: no." Stop there; skip `06 outcome`.

Disagree with something it does? Say so as Sam would, and note it. That's a finding too.

## What to report
Copy this and fill it in:

```
Agent and model:
Time the agent took (start to numbered request):
Time you spent (setup and answering Sam):
Did it finish and number a request (05 request/14-example-crescent/vpo-request-1.pdf)? yes / no
Request totals: before tax $____  tax $____  total $____
Did it stop on the PO that appears twice? yes / no
Questions it asked Sam beyond the 5 above (how many, and what):
Every place it got stuck, guessed or failed (file and line if you can):
Anything it did that Sam would refuse:
Would a painter use this as it is? yes / no, and why, in one line:
One sentence I may quote, with your name:
May I use your quote and your numbers in my pitch and on Demo Day, with your name? yes / no
```

Post it in the Lyceum Discord, channel **Shark Tank Testing**, as a reply to my post, or open an
issue on this repo. I'll reply the same day saying, line by line, whether your totals are right.

## The answer key is sealed
The right numbers for 14 Example Crescent are in an answer key worked out separately, and kept
private so your run isn't steered. Its SHA-256 fingerprint, also posted in the Discord thread so it
is dated somewhere I can't edit:

```
db3ce7f853bfea00a1d1c82c707986a1251ba0b6ad957e78cc7cee86e3a7dda4
```

Once 3 testers have reported, the key is published here. Run `sha256sum` (or
`Get-FileHash` on Windows) on it to check it is the file sealed on 2026-10-25.

## Already known (find something new)
- The agent still lays out the request page and types its numbers. The script works every figure
  out again from Sam's approved records and refuses to number a request where any differs, but it
  does not yet write the page itself.
- Nothing stops an agent from changing a file in `01 intake`; it is held by the rules only.
- Sam's yes is written into each file by the agent. The script checks that a yes is there and
  that every figure agrees with it, but an agent that edits an approved file, or writes a yes Sam
  never gave, is stopped only by the rules and by Sam reading his records.
- The rule that the agent does not read `README.md` or `_for-testers/` is a sentence in
  `CLAUDE.md`, not a lock.
- `06 outcome` has not been walked as far as the others.
- Tested on Windows. Mac and Linux are expected to work but have not been run end to end.
