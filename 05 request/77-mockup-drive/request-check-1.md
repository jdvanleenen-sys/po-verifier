---
house: 77-mockup-drive
attempt: 1
stage: 05 request
from: 04 review/77-mockup-drive/review-1.md, 03 compare/77-mockup-drive/variance-1.md
request: vpo-request-1.pdf
---

# 77-mockup-drive, request check 1

Copy to `05 request/<house>/request-check-N.md`. Line format as in `templates/request-check.md`
(its format sentence is left out here because its sample failing line trips the commit script's
fail-line search).

Checks 1 to 4 were run by a script that read the draft PDF's text back with PyMuPDF (Decimal arithmetic), 2026-10-17.

1. Only approved rows, and all of them: pass: the PDF carries 2 rows, "8' doors and trim" (PO MKR-02402401/027) and "Prime and paint garage, including ceiling" (no PO); review-1 has exactly these 2 rows "on". The stringer row (review-1 "off") and the four $0.00 rows are not on the PDF.
2. Each difference matches the variance: pass: 8' doors and trim +$300.00 on the PDF = +$300.00 in variance-1; garage +$672.00 on the PDF = +$672.00 in variance-1.
3. Tax per PO, from its own printed rate: pass: PO /027 rate 491.55 / 9831.00 = 0.05 GST/HST, PST 0.00 / 9831.00 = 0; 300.00 x 0.05 = 15.00, 300.00 + 15.00 = 315.00, as printed. No PO group: /012 (50/1000), /027 (491.55/9831) and /041 (25/500) all 0.05 and PST 0, so one rate; 672.00 x 0.05 = 33.60, 672.00 + 33.60 = 705.60, as printed. No $0.00 PST line is shown; the tax note says PST was $0.00.
4. House totals add up: pass: before tax 300.00 + 672.00 = 972.00 (PDF $972.00); tax 15.00 + 33.60 = 48.60 (PDF $48.60); total 972.00 + 48.60 = 1,020.60 (PDF $1,020.60), equal to the group totals 315.00 + 705.60 = 1,020.60.
5. Every proof document attached (from script-checks.md): pass: 4 file(s) merged after the request (PO MKR-02402401-012.html, PO MKR-02402401-027.html, PO MKR-02402401-041.html, site-notes.txt); 5 pages in all.
6. Page count printed equals actual pages, footer on the last page (from script-checks.md): pass: prints 'page 1 of 1'; the request has 1 page(s). Footer: pass: the sign-off footer is on the last request page (1).

## Sam's yes to send
- Answer: yes, to vpo-request-1.pdf as shown
- Name: Sam
- Date: 2026-10-17
- sent: no (practice run; nothing has been sent to the builder or the site super)
