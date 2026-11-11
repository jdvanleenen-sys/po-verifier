"""Printing for the request: find a browser, print HTML to PDF, count pages, merge the proof."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf

# The layout prints this mark once, where the page line goes; build_request fills it with page_words.
PAGE_MARK = "{{PAGE_LINE}}"
# Chrome first: Edge has hung on headless printing in testing (2026-10-27); Chrome did not.
BROWSER_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
BROWSER_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "microsoft-edge", "microsoft-edge-stable", "chrome", "msedge"]


def find_browser():
    """BROWSER if set, then the usual install paths, then anything on the PATH by name."""
    candidates = [os.environ.get("BROWSER", "").strip().strip('"')] + BROWSER_PATHS
    candidates += [shutil.which(name) or "" for name in BROWSER_NAMES]
    for path in candidates:
        if path and Path(path).is_file():
            return path
    sys.exit("No Chrome, Chromium or Edge found. Install Chrome, or set BROWSER to your browser's full path.")


def temp_profile():
    """A throwaway browser profile. ignore_cleanup_errors needs Python 3.10, so fall back without it."""
    try:
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    except TypeError:
        return tempfile.TemporaryDirectory()


def print_pdf(browser, html_path, pdf_path, tries=3):
    """Print one HTML file to PDF, headless, no browser header or footer. Retries a hung print."""
    for _ in range(tries):
        pdf_path.unlink(missing_ok=True)
        with temp_profile() as profile:
            cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                   f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}",
                   html_path.resolve().as_uri()]
            try:
                subprocess.run(cmd, check=False, capture_output=True, timeout=60)
            except subprocess.TimeoutExpired:
                continue
        if pdf_path.is_file() and pdf_path.stat().st_size > 0:
            return
    sys.exit(f"The browser did not print {html_path.name} after {tries} tries. Nothing was kept. "
             "If this keeps happening, set BROWSER to Chrome's full path.")


def page_count(pdf_path):
    with pymupdf.open(pdf_path) as doc:
        return doc.page_count


def page_words(request_pages, proof_pages):
    """The page line: which pages are the request, and how many proof pages the file holds after it,
    so a builder holding a 6-page file is not told "page 1 of 1"."""
    def pages(n):
        return f"{n} page" + ("" if n == 1 else "s")
    return (f"Request page 1 of {request_pages}. Proof attached: {pages(proof_pages)} "
            f"({pages(request_pages + proof_pages)} in this file).")


def print_request(browser, draft, proof_pages):
    """Print the request twice: once to count pages, once with the real counts written in."""
    html = (draft / "request.html").read_text(encoding="utf-8")
    if PAGE_MARK not in html:
        sys.exit(f"request.html has no {PAGE_MARK} placeholder (an older layout said 'page 1 of "
                 "{{PAGES}}'). Copy the layout again.")
    counting, first = draft / "_count.html", draft / "_count.pdf"
    counting.write_text(html.replace(PAGE_MARK, page_words(9, proof_pages)), encoding="utf-8")
    print_pdf(browser, counting, first)
    pages = page_count(first)
    final_html = draft / "_final.html"
    final_html.write_text(html.replace(PAGE_MARK, page_words(pages, proof_pages)), encoding="utf-8")
    request_pdf = draft / "request-only.pdf"
    print_pdf(browser, final_html, request_pdf)
    for tmp in (counting, first, final_html):
        tmp.unlink(missing_ok=True)
    return request_pdf


def proof_pdf(browser, path, draft, notes=False):
    """Turn one proof document into a PDF in the draft folder and return its path. A notes file
    sent as a PDF gets its file name printed on every page, so check 5 finds it by name and no page
    of it passes for a PO's own page."""
    if path.suffix.lower() == ".pdf":
        return named_pages(path, draft / f"_proof-{path.stem}.pdf") if notes else path
    out = draft / f"_proof-{path.stem}.pdf"
    if path.suffix.lower() in (".html", ".htm"):
        print_pdf(browser, path, out)
        return out
    page = draft / f"_proof-{path.stem}.html"
    page.write_text(notes_page_html(path), encoding="utf-8")
    print_pdf(browser, page, out)
    page.unlink(missing_ok=True)
    return out


def named_pages(path, out):
    with pymupdf.open(path) as doc:
        for page in doc:
            page.insert_text((36, 20), path.name, fontsize=9)
        doc.save(out)
    return out


IMAGES = (".jpg", ".jpeg", ".png")


def notes_page_html(path):
    """One notes file as a printable page, headed by its file name so check 5 can find it.
    A photo is shown whole on the page as Sam took it; text is shown as written."""
    head = (f"<!doctype html><meta charset='utf-8'><title>{escape(path.name)}</title>"
            f"<h3 style='font-family:Arial'>{escape(path.name)}</h3>")
    if path.suffix.lower() in IMAGES:
        return head + (f"<img src='{path.resolve().as_uri()}' "
                       "style='max-width:100%;max-height:8.5in;object-fit:contain'>")
    text = path.read_text(encoding="utf-8", errors="replace")
    return head + f"<pre style='font-size:13px;white-space:pre-wrap'>{escape(text)}</pre>"


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def merge(request_pdf, proofs, out_pdf):
    """Request first, then each proof, into one PDF."""
    with pymupdf.open(request_pdf) as merged:
        for path in proofs:
            with pymupdf.open(path) as doc:
                merged.insert_pdf(doc)
        merged.save(out_pdf)
