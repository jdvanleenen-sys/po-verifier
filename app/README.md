# PO Checker phone app

One house from its POs and a notes photo to an approved, checked request PDF, from a phone on the
same Wi-Fi as the laptop that holds the folder. The folder does the work under its own rules; this
app only runs its steps in order and shows what it says. Spec: `docs/specs/2026-11-13-phone-app-design.md`.

## Quick start (Windows)
```
powershell -ExecutionPolicy Bypass -File app\start.ps1 -Folder "<the contractor's folder>"
```
It sets up the Python environment the first time, checks Claude Code is installed, and prints the
link for the phone. The steps it runs are below.

## Set up once (Windows)
```
python -m venv --system-site-packages .venv
.venv\Scripts\python -m pip install -r app/requirements.txt
```
`--system-site-packages` lets the app use the PyMuPDF the folder's request stage already needs.
The read and the request layout run Claude Code headless on this laptop's own login: `claude` must
be on the PATH and signed in. No API key.

## Start it
```
.venv\Scripts\python app/server.py --folder "<the contractor's folder>"
```
It prints a link such as `http://192.168.x.x:8000/?k=...`. Open it on the phone. The `k` key is
new each start; the phone keeps it for 30 days after the first visit, but a restart needs the new
link. Without the key the app answers nothing. If the phone cannot reach the laptop, allow Python
through the Windows firewall on private networks.

## What it writes
- `01 intake/real-N/` once, at Lock, from the upload and Sam's answers. Never again.
- The stage records, only through the folder's own scripts (`grid.py`, `seal.py`, `compare.py`,
  `build_request.py`) or the headless agent following the stage's `CONTEXT.md`.
- Its own notes in `_app/` in the folder: uploads waiting to be locked, Sam's answers before the
  read, his notes answer, and each job's state, so a restart picks up where it was.

## Parts
| File | Job |
|---|---|
| `start.ps1` | Set up on first start, check the laptop and the folder, start the server |
| `server.py` | Routes only |
| `config.py` | Settings: the agent command, time limits, accepted file types and size |
| `folder.py` | The folder being driven: its stage paths, its own scripts, its house list |
| `steps.py` | Each step of a house in order; each checks the files first, so nothing runs twice |
| `house_view.py` | What each screen shows and what each tap does |
| `houses.py` | Which screen a house is on, read from its files every time |
| `lock.py`, `po_address.py` | New house: hold the uploads, ask before the read, lock into intake |
| `jobs.py`, `agent.py`, `prompts/` | One headless agent job per house, with Stop and a time limit |
| `questions.py`, `sam_yes.py` | Check screen cards; Sam's yes written and sealed by `seal.py` |
| `difference.py` | Difference screen rows and the review file |
| `request_pdf.py` | The draft request's six checks, Approve, sent |
| `static/` | The seven screens |

No module here may share a name with a stage script (`tests/test_app_names.py`).
