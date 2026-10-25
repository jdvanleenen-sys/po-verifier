"""Print, check and number a VPO request, the same way every time.

Two commands, run from the PO Verifier folder:

  python "05 request/build_request.py" build <house>
      Reads   05 request/drafts/<house>/request.html  (the filled-in layout)
      Prints  it to PDF, counts the pages, writes "page 1 of N" from that count, prints again.
      Merges  the proof from 01 intake/<house>/ (each PO, then the site notes) after the request.
      Checks  the parts a script can check (page count, footer, proof attached) and writes
              05 request/drafts/<house>/script-checks.md
      Nothing is written into the house folder. A failed print leaves no trace in the record.

  python "05 request/build_request.py" commit <house>
      Only after the AI has added its own checks to drafts/<house>/request-check.md and none of
      the lines says "fail": copies the draft PDF and the check file into
      05 request/<house>/ as the next number, vpo-request-N.pdf and request-check-N.md.

Needs: Python 3, PyMuPDF (pip install pymupdf), and Microsoft Edge or Google Chrome.
Set the BROWSER environment variable to the browser's path if it is somewhere unusual.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parent
PAGE_MARK = "{{PAGES}}"
FOOTER_TEXT = "Checked and approved by"
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def find_browser():
    """Return the first browser that exists, or stop with a plain message."""
    candidates = [os.environ.get("BROWSER", "")] + BROWSERS
    for path in candidates:
        if path and Path(path).is_file():
            return path
    sys.exit("No Edge or Chrome found. Set BROWSER to the browser's full path.")


def print_pdf(browser, html_path, pdf_path, tries=3):
    """Print one HTML file to PDF, headless, no browser header or footer. Retries a hung print."""
    for _ in range(tries):
        pdf_path.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
            cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                   f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}",
                   html_path.resolve().as_uri()]
            try:
                subprocess.run(cmd, check=False, capture_output=True, timeout=60)
            except subprocess.TimeoutExpired:
                continue
        if pdf_path.is_file() and pdf_path.stat().st_size > 0:
            return
    sys.exit(f"The browser did not print {html_path.name} after {tries} tries. Nothing was kept.")


def page_count(pdf_path):
    with pymupdf.open(pdf_path) as doc:
        return doc.page_count


def print_request(browser, draft):
    """Print the request twice: once to count pages, once with the real count written in."""
    source = draft / "request.html"
    html = source.read_text(encoding="utf-8")
    if PAGE_MARK not in html:
        sys.exit(f"request.html has no {PAGE_MARK} placeholder. Copy the layout again.")
    counting = draft / "_count.html"
    counting.write_text(html.replace(PAGE_MARK, "9"), encoding="utf-8")
    first = draft / "_count.pdf"
    print_pdf(browser, counting, first)
    pages = page_count(first)
    final_html = draft / "_final.html"
    final_html.write_text(html.replace(PAGE_MARK, str(pages)), encoding="utf-8")
    request_pdf = draft / "request-only.pdf"
    print_pdf(browser, final_html, request_pdf)
    for tmp in (counting, first, final_html):
        tmp.unlink(missing_ok=True)
    return request_pdf, pages


def proof_files(house):
    """The proof for a house: each PO and EPO in intake, in name order, then the site notes."""
    intake = ROOT / "01 intake" / house
    if not intake.is_dir():
        sys.exit(f"No intake folder for {house}.")
    docs = sorted(p for p in intake.iterdir() if p.suffix.lower() in (".html", ".htm", ".pdf"))
    notes = sorted(p for p in intake.iterdir() if p.name.lower().startswith("site-notes"))
    return docs + notes


def proof_pdf(browser, path, draft):
    """Turn one proof document into a PDF in the draft folder and return its path."""
    if path.suffix.lower() == ".pdf":
        return path
    out = draft / f"_proof-{path.stem}.pdf"
    if path.suffix.lower() in (".html", ".htm"):
        print_pdf(browser, path, out)
        return out
    text = path.read_text(encoding="utf-8", errors="replace")
    safe = text.replace("&", "&amp;").replace("<", "&lt;")
    page = draft / f"_proof-{path.stem}.html"
    page.write_text(f"<!doctype html><meta charset='utf-8'><title>{path.name}</title>"
                    f"<h3 style='font-family:Arial'>{path.name}</h3>"
                    f"<pre style='font-size:13px'>{safe}</pre>", encoding="utf-8")
    print_pdf(browser, page, out)
    page.unlink(missing_ok=True)
    return out


def merge(request_pdf, proofs, out_pdf):
    """Request first, then each proof. Returns the number of proof pages added per file."""
    added = []
    with pymupdf.open(request_pdf) as merged:
        for path in proofs:
            with pymupdf.open(path) as doc:
                merged.insert_pdf(doc)
                added.append(doc.page_count)
        merged.save(out_pdf)
    return added


def request_text(request_pdf):
    with pymupdf.open(request_pdf) as doc:
        return [page.get_text() for page in doc]


def script_checks(request_pdf, pages, proofs, added, merged_pdf):
    """The checks a script can do. Each line: pass, fail or cannot check, with its evidence."""
    texts = request_text(request_pdf)
    lines = []
    printed = re.search(r"page 1 of (\d+)", texts[0])
    if printed and int(printed.group(1)) == pages:
        lines.append(f"6. Page count: pass: prints 'page 1 of {pages}'; the request has {pages} page(s).")
    else:
        shown = printed.group(0) if printed else "no 'page 1 of N' found on page 1"
        lines.append(f"6. Page count: fail: {shown}; expected: page 1 of {pages}.")
    footer_page = next((i + 1 for i, t in enumerate(texts) if FOOTER_TEXT in t), None)
    if footer_page == pages:
        lines.append(f"6b. Footer: pass: the sign-off footer is on the last request page ({pages}).")
    else:
        lines.append(f"6b. Footer: fail: footer found on page {footer_page}; expected: page {pages}.")
    total = page_count(merged_pdf)
    expected = pages + sum(added)
    names = ", ".join(p.name for p in proofs)
    if total == expected and all(n > 0 for n in added):
        lines.append(f"5. Proof attached: pass: {len(proofs)} file(s) merged after the request "
                     f"({names}); {total} pages in all.")
    else:
        lines.append(f"5. Proof attached: fail: {total} pages; expected: {expected}.")
    return lines


def build(house):
    draft = STAGE / "drafts" / house
    if not (draft / "request.html").is_file():
        sys.exit(f"Put the filled-in layout at 05 request/drafts/{house}/request.html first.")
    for old in ("vpo-request.pdf", "request-only.pdf", "script-checks.md", "request-check.md"):
        (draft / old).unlink(missing_ok=True)
    browser = find_browser()
    request_pdf, pages = print_request(browser, draft)
    proofs = proof_files(house)
    proof_pdfs = [proof_pdf(browser, p, draft) for p in proofs]
    merged_pdf = draft / "vpo-request.pdf"
    added = merge(request_pdf, proof_pdfs, merged_pdf)
    for tmp in draft.glob("_proof-*.pdf"):
        tmp.unlink()
    lines = script_checks(request_pdf, pages, proofs, added, merged_pdf)
    report = draft / "script-checks.md"
    report.write_text(f"# {house}, script checks\n\n" + "\n".join(f"- {l}" for l in lines) + "\n",
                      encoding="utf-8")
    print("\n".join(lines))
    print(f"Draft: {merged_pdf.relative_to(ROOT)}")
    return 0 if all(": pass:" in l for l in lines) else 1


FINDING = re.compile(r"^[-*\s]*\d+[a-z]?\.\s.*?\b(pass|fail|cannot check):", re.IGNORECASE | re.MULTILINE)


def findings(path):
    """Count findings on numbered check lines only, so instructions in a form are never counted."""
    counts = {"pass": 0, "fail": 0, "cannot check": 0}
    for word in FINDING.findall(path.read_text(encoding="utf-8")):
        counts[word.lower()] += 1
    return counts


def next_number(house_dir):
    taken = [int(m.group(1)) for p in house_dir.glob("vpo-request-*.pdf")
             if (m := re.match(r"vpo-request-(\d+)\.pdf$", p.name))]
    return max(taken, default=0) + 1


def commit(house):
    draft = STAGE / "drafts" / house
    pdf, check = draft / "vpo-request.pdf", draft / "request-check.md"
    for need in (pdf, check, draft / "script-checks.md"):
        if not need.is_file():
            sys.exit(f"Missing {need.relative_to(ROOT)}. Run build, then write the request check.")
    if findings(draft / "script-checks.md")["fail"]:
        sys.exit("The script checks failed. Fix the draft and build again. Nothing was numbered.")
    if pdf.stat().st_mtime < (draft / "request.html").stat().st_mtime:
        sys.exit("request.html changed after the last build. Build again. Nothing was numbered.")
    if check.stat().st_mtime < pdf.stat().st_mtime:
        sys.exit("request-check.md is older than the last build. Check the new draft. Nothing was numbered.")
    found = findings(check)
    if found["fail"]:
        sys.exit("The request check has a fail line. Nothing was numbered.")
    if found["pass"] + found["cannot check"] < 6:
        sys.exit("The request check does not cover all six checks. Nothing was numbered.")
    house_dir = STAGE / house
    house_dir.mkdir(exist_ok=True)
    n = next_number(house_dir)
    shutil.copy2(pdf, house_dir / f"vpo-request-{n}.pdf")
    shutil.copy2(check, house_dir / f"request-check-{n}.md")
    print(f"Numbered as 05 request/{house}/vpo-request-{n}.pdf and request-check-{n}.md")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("build", "commit"):
        sys.exit(__doc__)
    sys.exit(build(sys.argv[2]) if sys.argv[1] == "build" else commit(sys.argv[2]))
