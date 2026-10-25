# Testing the PO Verifier

Thank you for testing. The goal is to find where it breaks, so a finding is worth more than a
pass. About 30 to 45 minutes.

## What you need
- An AI coding agent that works in a folder, such as Claude Code. It reads `CLAUDE.md` first.
- Python 3 with PyMuPDF: `pip install pymupdf`
- Google Chrome or Microsoft Edge, for printing the request to PDF. If yours is somewhere unusual,
  set `BROWSER` to its full path.

Work in your own copy of this repo. Nothing in it is real, and nothing gets sent.

## The job
Open the folder in your agent and give it this, word for word:

> Sam just dropped in a new house, 14 Example Crescent. Run it through the folder and build the
> request for the difference.

Then let it work. **Give it no other hints**: the test is whether the folder alone gets it there.
`77-mockup-drive` is a house that has already been run; leave it as it is.

## You play Sam
Sam is the painter. The agent will stop and ask him things. Answer as Sam, using these answers,
so every tester's run can be compared:

- **If it asks about a PO that appears twice:** "That's the same PO downloaded twice. Read it
  once, and leave both files in intake."
- **When it shows the read-back table:** check it against the POs and Sam's site notes. If it
  matches, say "Yes, to the whole table." If something is wrong, say what, as Sam would.
- **At review:** "Include the French door credit. Chase the 8' doors. Leave the stringers and the
  headers off. Keep the other flagged rows on. Yes, to the table with those decisions."
- **At the end, when it asks if this is the request he will send:** "Yes, but this is practice,
  so it is not being sent. Write sent: no." Stop there; skip `06 outcome`.

Disagree with something it does? Say so as Sam would, and note it. That's a finding too.

## What to report
Copy this and fill it in:

```
Agent and model:
Time taken:
Did it finish and number a request (05 request/14-example-crescent/vpo-request-1.pdf)? yes / no
Request totals: before tax $____  tax $____  total $____
Did it stop on the PO that appears twice? yes / no
Files it read before it knew where to go:
Every place it got stuck, guessed or asked you something unexpected (file and line if you can):
Anything it did that Sam would refuse:
Anything you'd change:
```

Post it in the Shark Tank Testing thread, or open an issue on this repo.

## The answer key is sealed
The right numbers for 14 Example Crescent are in an answer key worked out separately, and kept
private so your run isn't steered. Its SHA-256 fingerprint is:

```
db3ce7f853bfea00a1d1c82c707986a1251ba0b6ad957e78cc7cee86e3a7dda4
```

Once 3 testers have reported, the key is published here. Run `sha256sum` (or
`Get-FileHash` on Windows) on it to check it is the same file that was sealed today, 2026-10-25.

## Already known (find something new)
- A PO saved twice is caught and stops the run, but both copies still go to the builder as proof
  (`05 request/build_request.py`, the proof list attaches every PO file in intake).
- A row that is both flagged and a credit falls under 2 defaults that disagree
  (`04 review/CONTEXT.md`, the flagged-rows rule and the credits rule).
- No rule says how a duplicate PO is settled, and the read-back form has no place to record it.
- The request script checks pages, the footer and the proof. It does not re-add the dollars;
  the agent's own written check does that.
- Nothing stops an agent from changing a file in `01 intake`; it is held by the rules only.
- `06 outcome` has not been walked as far as the others.
