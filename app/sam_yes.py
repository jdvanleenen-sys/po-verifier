"""Sam's yes written in the folder's own format, then sealed by the folder's own seal.py. The runner
writes a yes only after Sam taps for it, and never sets status: approved itself."""
import re
import subprocess
import sys

YES_HEADING = "## Sam's yes"
FIELD = {"Answer": re.compile(r"^-\s*Answer:.*$", re.M), "Name": re.compile(r"^-\s*Name:.*$", re.M),
         "Date": re.compile(r"^-\s*Date:.*$", re.M)}
NAME_LINE = re.compile(r"^-\s*Name:[ \t]*(\S.*)$", re.M)


class Refused(Exception):
    """The folder refused; the message is the folder's own reason."""


def script(folder, stage_script, *args):
    """Run one of the folder's scripts from its top level. Returns (passed, output)."""
    done = subprocess.run([sys.executable, stage_script, *args], cwd=folder.root, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    return done.returncode == 0, (done.stdout + done.stderr).strip()


def painter_name(folder):
    """The name his yes is written under: the Name line in reference/contractor.md."""
    found = NAME_LINE.search((folder.root / "reference" / "contractor.md").read_text(encoding="utf-8"))
    if not found:
        raise Refused("reference/contractor.md has no Name line, so a yes cannot be written under a name.")
    return found.group(1).strip()


def write_yes(path, name, day):
    """Fill the Sam's yes block of a draft record with a plain yes, his name and the date."""
    text = path.read_text(encoding="utf-8")
    if YES_HEADING not in text:
        raise Refused(f"{path.name} has no \"Sam's yes\" block to write his yes in.")
    head, block = text.split(YES_HEADING, 1)
    for field, value in (("Answer", "yes"), ("Name", name), ("Date", day)):
        if not FIELD[field].search(block):
            raise Refused(f"{path.name}'s \"Sam's yes\" block has no {field} line.")
        block = FIELD[field].sub(f"- {field}: {value}", block, count=1)
    path.write_text(head + YES_HEADING + block, encoding="utf-8", newline="\n")


def seal(folder, path, name, day):
    """Write the yes and seal. If seal.py refuses, the yes is taken back out and Refused carries the
    folder's reason, so a refused record is left as the draft it was."""
    before = path.read_text(encoding="utf-8")
    write_yes(path, name, day)
    passed, output = script(folder, "02 read/seal.py", str(path.relative_to(folder.root)))
    if not passed:
        path.write_text(before, encoding="utf-8", newline="\n")
        raise Refused(output or "seal.py refused the record.")
    return output
