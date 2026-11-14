You are running the PO Verifier folder in the current directory, with no one to talk to. Read CLAUDE.md first and follow it.

Task: run stage 02 read for the house {house}. Its files are in `01 intake/{house}/`. Follow `02 read/CONTEXT.md` exactly.

Sam answered these before the read, on the app's New house screen. Write each into the read-back the way the stages say Sam's answers are written (never into `01 intake`), and do not ask them again:
{answers}

Write `02 read/{house}/read-back-1.md`, build its grid with `python "02 read/grid.py" build {house}`, answer every `?` cell the stage lets you answer, then run `python "02 read/grid.py" check {house}`. Run every command from this folder's top level; never start a command with cd.

Stop when the draft read-back and its grid are written and checked. Do not seal anything, do not write a yes for Sam, and do not start 03 compare or any later stage. Do not ask questions in chat: every other question for Sam goes into the read-back and the grid the way the stage says (`ask Sam:` cells, the warning table). Never change anything in `01 intake`. Never read or write the `_app` folder.

End with one line only: `DONE {house} read-back-1, N questions for Sam` or `STOPPED: <the reason>`.
