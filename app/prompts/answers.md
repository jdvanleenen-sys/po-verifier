You are running the PO Verifier folder in the current directory, with no one to talk to. Read CLAUDE.md first and follow it.

Task: house {house} is in stage 02 read. Sam answered the open questions in `02 read/{house}/{read_back}` on the app's Check screen. Follow `02 read/CONTEXT.md` exactly ("How Sam confirms", "Standing answers", "Warning: not on the price list") to write the next numbered read-back, `02 read/{house}/{next_read_back}`, from that one with his answers in it, then build its grid with `python "02 read/grid.py" build {house}`, answer every `?` cell the stage lets you answer, and run `python "02 read/grid.py" check {house}`.

Sam's answers, in his words, given {today}:
{answers}

Run every command from this folder's top level; never start a command with cd. Do not seal anything, do not write a yes for Sam, and do not start 03 compare or any later stage. If an answer raises a new question, put it in the read-back and grid the way the stage says; do not ask in chat and do not guess. Never change anything in `01 intake`. Never read or write the `_app` folder.

End with one line only: `DONE {house} {next_read_back_stem}, N questions for Sam` or `STOPPED: <the reason>`.
