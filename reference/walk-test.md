# Walk test

Run this cold, as a fresh AI with only this folder. Each line is yes or no. A no is a line the
folder still needs.

1. From `CLAUDE.md` and `CONTEXT.md` alone, can you say where a house goes first and what each
   stage is for?
2. Does every file in the folder appear in the map in `CONTEXT.md`?
3. Does each stage's `CONTEXT.md` name its exact input, its job, its output file, and where Sam is
   asked?
4. Can you tell where a house stands just by looking at which numbered files exist?
5. Does `03 compare` read only the highest-numbered read-back and `reference/contractor.md`?
6. Does every rate in the compare come from the read-back, with the price list date recorded in it?
7. Is there any place where a stage could go on without Sam's written yes?
8. Is any output overwritten instead of numbered?
9. Is any fact stored in two places? Pick one home and point to it from the other.
10. Does anything in the folder say it was approved when nobody approved it?
11. Does `05 request` check the finished PDF before Sam sees it?
12. Does every outcome file end up as one line in `06 outcome/ledger.md`, and can every sent
    request be found by its `sent: yes`?
13. Does each stage's output follow its form in `templates/`?
14. Is the request PDF made by `05 request/build_request.py`, in `drafts/` first, and numbered only
    after all six checks pass?
