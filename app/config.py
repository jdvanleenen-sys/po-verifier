"""Settings for the runner. Change them here, never in the code that uses them."""
import os
import shutil

# The headless agent. PO_APP_AGENT replaces it (tests point it at a stand-in that calls no model).
AGENT_COMMAND = os.environ.get("PO_APP_AGENT", "").split("|") if os.environ.get("PO_APP_AGENT") else [
    shutil.which("claude") or "claude", "-p", "--output-format", "json", "--permission-mode", "acceptEdits",
    "--allowedTools", "Bash(python:*)", "Read", "Write", "Edit", "Glob", "Grep"]

# Measured 2026-11-14: a read 2.5 to 4 min, an answer round 2 to 3.5 min, the request build 9.5 min.
# Past this, the screen offers Keep waiting or Stop.
READ_WARN_SECONDS = 15 * 60
# Past this the run is stopped and the house stays at its last good step.
READ_LIMIT_SECONDS = 30 * 60

PO_TYPES = (".pdf", ".html", ".htm", ".jpg", ".jpeg", ".png")
NOTES_TYPES = (".jpg", ".jpeg", ".png", ".pdf", ".txt")
MAX_FILE_BYTES = 25 * 1024 * 1024

# The runner's own records (uploads waiting to be locked, Sam's answers before the read, jobs).
# Kept in the folder so a restart finds them; the leading underscore keeps it out of the house list.
APP_DIR = "_app"
