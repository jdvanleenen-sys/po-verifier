"""Print, check and number a VPO request, the same way every time.

Two commands, run from the PO Verifier folder:

  python "05 request/build_request.py" build <house> --notes yes|no
      --notes is Sam's answer to "attach your site notes as proof?" Ask him first.
      Checks  Sam's approved read-back and review, and the variance, before anything is printed.
      Prints  05 request/drafts/<house>/request.html to PDF with "page 1 of N" from the real count.
      Merges  the proof from 01 intake/<house>/: each PO and EPO once (a file saved twice is
              attached once), then the site notes only if Sam said yes. Any other file is named,
              never silently sent.
      Checks  all six request checks on the PDF itself (verify.py) and writes
              05 request/drafts/<house>/script-checks.md. Nothing is written into the house folder.

  python "05 request/build_request.py" commit <house>
      Runs all six checks again on the draft PDF, from Sam's records, trusting no written check.
      Only if every one passes: copies it to 05 request/<house>/vpo-request-N.pdf and writes
      request-check-N.md (the six findings, then Sam's yes to send, left blank for him).

Needs: Python 3.9+, PyMuPDF (pip install pymupdf), and Google Chrome, Chromium or Microsoft Edge.
Set the BROWSER environment variable to the browser's path if it is somewhere unusual.
"""
import argparse
import hashlib
import html
import re
import shutil
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parent
sys.path.insert(0, str(STAGE))
import house_checks  # noqa: E402
import money  # noqa: E402
import printing  # noqa: E402
import verify  # noqa: E402
from chain import chain_problems  # noqa: E402  (money puts 02 read on the path)
import seal  # noqa: E402

DOCS = (".html", ".htm", ".pdf")
NOTES = (".txt", ".md", ".jpg", ".jpeg", ".png", ".pdf")
NOTES_NAMES = ("note", "voice-memo", "checklist", "measurement")
NOT_PROOF = ("house-info.md",)
ONLY = "only:"


def latest(folder, stem):
    """The highest-numbered <stem>-N.md in a folder."""
    found = [(int(m.group(1)), p) for p in folder.glob(f"{stem}-*.md")
             if (m := re.match(rf"{stem}-(\d+)\.md$", p.name))]
    return max(found)[1] if found else None


def grid_path(read_back_path):
    """The rule grid built for a read-back: read-back-N.md has grid-N.md beside it."""
    return read_back_path.with_name(read_back_path.name.replace("read-back-", "grid-", 1))


def record_stop(paths, texts):
    """Stop when an approved record carries another file's seal or its numbering is broken."""
    problems = []
    for key, path in paths.items():
        if key != "variance":
            problems += [f"{path.name} {why}" for why in seal.seal_problems(texts[key], path.name)
                         if "copied under a new name" in why]
            problems += [f"{path.name} {why}" for why in seal.ledger_problems(path, texts[key])]
        problems += chain_problems(path, texts[key], ROOT)
    if problems:
        sys.exit("Sam's records are not in order, so nothing was built:\n- " + "\n- ".join(problems))


def records(house):
    """The approved review, the variance it names, and the read-back that variance names."""
    review = latest(ROOT / "04 review" / house, "review")
    if review is None:
        sys.exit(f"No review for {house} in 04 review/. Nothing was built.")
    texts = {"review": money.read_text(review)}
    paths = {"review": review}
    named = {"variance": ("03 compare", "variance"), "read-back": ("02 read", "read-back")}
    source = texts["review"]
    for key, (stage, stem) in named.items():
        match = re.search(rf"{re.escape(stage)}/{re.escape(house)}/({stem}-\d+\.md)", source)
        path = ROOT / stage / house / match.group(1) if match else latest(ROOT / stage / house, stem)
        if match and not path.is_file():
            sys.exit(f"The {key} named in the record before it, {stage}/{house}/{match.group(1)}, does not "
                     "exist. Nothing was built.")
        if path is None or not path.is_file():
            sys.exit(f"No {key} for {house} in {stage}/. Nothing was built.")
        texts[key] = source = money.read_text(path)
        paths[key] = path
    record_stop(paths, texts)
    grid = grid_path(path)
    texts["grid"] = money.read_text(grid) if grid.is_file() else None
    texts["price-list"] = money.prices.snapshot_bytes(house, texts["read-back"])
    return texts


def intake(house):
    """PO and EPO files (each saved file once), the site notes file, and anything else."""
    folder = ROOT / "01 intake" / house
    if not folder.is_dir():
        sys.exit(f"No intake folder for {house}.")
    docs, seen, notes, others = [], {}, [], []
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() in NOTES and any(n in p.name.lower() for n in NOTES_NAMES):
            notes.append(p)  # before POs: a painter's checklist can come as a PDF
        elif p.suffix.lower() in DOCS:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest in seen:
                others.append(f"{p.name} (the same file as {seen[digest]}, attached once)")
            else:
                seen[digest] = p.name
                docs.append(p)
        elif p.name.lower() not in NOT_PROOF:
            others.append(f"{p.name} (not a PO, EPO or notes file, not attached)")
    return docs, notes, others


def choose_notes(notes, choice):
    """Sam's answer to "attach your notes?": yes (all of them), no, or only:<file>,<file>."""
    if choice == "yes":
        return list(notes)
    if choice == "no":
        return []
    if not choice.startswith(ONLY):
        sys.exit("--notes must be yes, no, or only:<file name>,<file name>. Nothing was built.")
    names = [n.strip() for n in choice[len(ONLY):].split(",") if n.strip()]
    by_name = {p.name: p for p in notes}
    missing = [n for n in names if n not in by_name]
    if missing or not names:
        sys.exit(f"Sam named notes that are not in intake: {', '.join(missing) or '(none named)'}. "
                 f"The notes files are: {', '.join(by_name) or 'none'}. Nothing was built.")
    return [by_name[n] for n in names]


def proof_spec(expected, attached, notes):
    """What must be in the proof, and the notes pages Sam left out, which must not be."""
    names = [p.name for p in attached]
    return {"po_numbers": expected["po_numbers"], "epo_names": expected["epo_names"],
            "notes_attached": names, "notes_left_out": [p.name for p in notes if p.name not in names]}


JOB_NAME = re.compile(r"JOB NAME:\s*(.*?)\s+JOB ADDRESS:")


def document_text(path):
    """A PO or EPO file's text: tags dropped from HTML, the text layer of a PDF."""
    if path.suffix.lower() == ".pdf":
        return " ".join(verify.pdf_pages(path) or [])
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", money.read_text(path))))


def header_spec(house, n):
    """What the request's header must say: the document number this commit gives, the numbers in
    house-info's address and lot (None if house-info has neither), and each PO's job name."""
    folder = ROOT / "01 intake" / house
    info = money.read_text(folder / "house-info.md") if (folder / "house-info.md").is_file() else ""
    fields = [m.group(1) for f in ("address", "lot") if (m := re.search(rf"^- {f}:\s*(.+)$", info, re.I | re.M))]
    texts = [document_text(p) for p in intake(house)[0]]
    if fields and not re.search(r"^- lot:", info, re.I | re.M) and (lot := house_checks.lot_from_pos(texts)):
        fields.append(" ".join(lot))
    names = {m.group(1).strip() for t in texts if (m := JOB_NAME.search(t))}
    measured = re.search(r"^- date measured:\s*(\d{4}-\d{2}-\d{2})\s*$", info, re.I | re.M)
    who = house_checks.contractor.read(ROOT / "reference" / "contractor.md")
    return {"contractor": who["shown"], "builders": who["builders"],"document": f"VR-{n:04d}", "job_numbers": [x for f in fields for x in re.findall(r"\d+", f)] if fields else None,
            "job_names": sorted(names), "measured": measured.group(1) if measured else None,
            **house_checks.header_extras(texts, money.read_text(r) if (r := latest(ROOT / "04 review" / house, "review")) else "")}


def review_name(house):
    review = latest(ROOT / "04 review" / house, "review")
    return f"04 review/{house}/{review.name}" if review else None


def stop_if_changed(house):
    """The contractor and intake checks: refused before anything is printed or numbered."""
    problems = house_checks.gate_problems(ROOT, house, records(house))
    if problems:
        sys.exit("Nothing was built or numbered:\n- " + "\n- ".join(problems))


def expected_or_stop(house):
    expected, problems = money.expected_request(records(house))
    if problems:
        sys.exit("Sam's records do not agree, so nothing was built:\n- " + "\n- ".join(problems) +
                 "\n" + house_checks.fix_advice(ROOT, house))
    return expected


def build(house, notes_choice):
    draft = STAGE / "drafts" / house
    if not (draft / "request.html").is_file():
        sys.exit(f"Put the filled-in layout at 05 request/drafts/{house}/request.html first.")
    expected = expected_or_stop(house)
    stop_if_changed(house)
    docs, notes, others = intake(house)
    if notes_choice != "no" and not notes:
        sys.exit("Sam said attach his site notes, but there is no notes file in intake.")
    attached = choose_notes(notes, notes_choice)
    for old in ("vpo-request.pdf", "request-only.pdf", "script-checks.md"):
        (draft / old).unlink(missing_ok=True)
    browser = printing.find_browser()
    request_pdf = printing.print_request(browser, draft)
    proofs = ([printing.proof_pdf(browser, p, draft) for p in docs]
              + [printing.proof_pdf(browser, p, draft, notes=True) for p in attached])
    merged = draft / "vpo-request.pdf"
    printing.merge(request_pdf, proofs, merged)
    for tmp in draft.glob("_proof-*.pdf"):
        tmp.unlink()
    lines = verify.run_checks(merged, expected, proof_spec(expected, attached, notes),
                              header_spec(house, next_number(STAGE / house)))
    left_out = [p.name for p in notes if p not in attached]
    report = [f"# {house}, script checks", "", *[f"- {l}" for l in lines], "",
              f"notes: {notes_choice}", f"pdf sha256: {house_checks.sha256(merged)}",
              f"html sha256: {house_checks.sha256(draft / 'request.html')}",
              *[f"not attached: {o}" for o in others],
              *[f"not attached: {n} (Sam left it out)" for n in left_out]]
    (draft / "script-checks.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(lines + [f"Not attached: {o}" for o in others]))
    print(f"Draft: {merged.relative_to(ROOT)}")
    return 0 if all(": pass:" in l for l in lines) else 1


def numbered_hashes(house_dir):
    return {hashlib.sha256(p.read_bytes()).hexdigest() for p in house_dir.glob("vpo-request-*.pdf")}


def next_number(house_dir):
    taken = [int(m.group(1)) for p in house_dir.glob("vpo-request-*.pdf")
             if (m := re.match(r"vpo-request-(\d+)\.pdf$", p.name))]
    return max(taken, default=0) + 1


def commit(house):
    draft = STAGE / "drafts" / house
    pdf, checks = draft / "vpo-request.pdf", draft / "script-checks.md"
    if not pdf.is_file() or not checks.is_file():
        sys.exit("Run build first. Nothing was numbered.")
    checks_text = money.read_text(checks)
    stale = house_checks.html_problem(draft / "request.html", checks_text)
    if stale:
        sys.exit(f"{stale} Nothing was numbered.")
    choice = re.search(r"^notes:\s*(yes|no|only:\S.*?)\s*$", checks_text, re.M)
    if not choice:
        sys.exit("script-checks.md does not record Sam's notes answer. Build again. Nothing was numbered.")
    changed = house_checks.pdf_problem(pdf, checks_text)
    if changed:
        sys.exit(f"{changed} Nothing was numbered.")
    expected = expected_or_stop(house)
    stop_if_changed(house)
    review = review_name(house)
    used = house_checks.review_used(STAGE / house, review)
    if used:
        sys.exit(f"{used} already comes from {review}. A new request needs a new review with Sam's yes. "
                 "Nothing was numbered.")
    _, notes, _ = intake(house)
    attached = choose_notes(notes, choice.group(1))
    house_dir = STAGE / house
    lines = verify.run_checks(pdf, expected, proof_spec(expected, attached, notes),
                              header_spec(house, next_number(house_dir)))
    if not all(": pass:" in l for l in lines):
        sys.exit("A check failed, so nothing was numbered:\n" + "\n".join(lines))
    house_dir.mkdir(exist_ok=True)
    if hashlib.sha256(pdf.read_bytes()).hexdigest() in numbered_hashes(house_dir):
        sys.exit("This exact request is already numbered. Nothing was numbered.")
    n = next_number(house_dir)
    shutil.copy2(pdf, house_dir / f"vpo-request-{n}.pdf")
    write_check(house_dir / f"request-check-{n}.md", house, n, lines, choice.group(1), review)
    print(f"Numbered as 05 request/{house}/vpo-request-{n}.pdf and request-check-{n}.md")
    return 0


def write_check(path, house, n, lines, notes, review):
    body = ["---", f"house: {house}", f"attempt: {n}", "stage: 05 request", f"request: vpo-request-{n}.pdf",
            f"from review: {review}",
            "checked by: 05 request/build_request.py (all six checks run by the script on the PDF)", "---", "",
            f"# {house}, request check {n}", "", *[f"- {l}" for l in lines], "",
            f"Site notes attached as proof: {notes}", "", "## Sam's yes to send",
            "- Answer:", "- Name:", "- Date:", "- sent: yes / no", ""]
    path.write_text("\n".join(body), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build, check and number a VPO request.")
    parser.add_argument("command", choices=["build", "commit"])
    parser.add_argument("house")
    parser.add_argument("--notes", help="Sam's answer: attach his site notes? yes, no, or only:<file>,<file>")
    args = parser.parse_args()
    if args.command == "build":
        if args.notes is None:
            sys.exit("Ask Sam first: attach your site notes as proof? Then add --notes yes, --notes no, "
                     "or --notes only:<file name> for just the pages he names.")
        return build(args.house, args.notes.strip())
    return commit(args.house)


if __name__ == "__main__":
    sys.exit(main())
