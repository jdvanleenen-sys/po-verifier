You are running the PO Verifier folder in the current directory, with no one to talk to. Read CLAUDE.md first and follow it.

Task: house {house} is in stage 05 request. The request's Prepared date is today, {today}. Sam's review is sealed. Follow `05 request/CONTEXT.md` exactly, steps 1 and 2 of "How the PDF is made" only:
1. Copy the layout to `05 request/drafts/{house}/request.html` and fill it in from the house's highest review and the variance it names, under "How it looks", "How the sums are done" and "Filling in the header".
2. Run `python "05 request/build_request.py" build {house} --notes {notes}` from this folder's top level. Sam already answered the notes question: `--notes {notes}`. If a check fails, fix only what that check names in the draft and build again: at most three builds, each judged against all six checks. If a check still fails after the third build, stop and end with `STOPPED:` and the failing check lines from `script-checks.md`.

Never run `commit`: Sam approves on his phone and the app numbers the request. Do not change any record in another stage, never change anything in `01 intake`, never read or write the `_app` folder, and never start a command with cd. Do not ask questions in chat.

End with one line only: `DONE {house} request built, six checks pass` or `STOPPED: <the reason>`.
