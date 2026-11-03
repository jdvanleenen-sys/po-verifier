"""Cold-run a test house through the folder, then score what came out. Run from the repo root.

    python tests/cold_run.py prepare <house> <empty folder>
        Copies the folder as a tester gets it, without tests/ (where the answer keys are) and
        without git, and drops the house's intake files into 01 intake/<house>/. Point a fresh
        agent at that copy and play Sam from tests/houses/<house>/sam-answers.md.

    python tests/cold_run.py score <house> <that folder>
        Reads what the run wrote and checks it against tests/houses/houses.json: the price check,
        every row's variance, the house total, and the request (or that there is none).

A score is only as good as the run: the agent must have had nothing but the copy and Sam's answers.
"""
import json
import re
import shutil
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOUSES = ROOT / "tests" / "houses"
LEAVE_OUT = shutil.ignore_patterns(".git", "tests", "__pycache__", "_for-testers", "drafts")


def spec(slug):
    for h in json.loads((HOUSES / "houses.json").read_text(encoding="utf-8"))["houses"]:
        if h["slug"] == slug:
            return h
    sys.exit(f"No test house called {slug}.")


def prepare(slug, dest):
    spec(slug)
    dest = Path(dest)
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f"{dest} is not empty. Give an empty or new folder.")
    if ROOT in dest.resolve().parents or dest.resolve() == ROOT:
        sys.exit("The copy must be outside this folder.")
    shutil.copytree(ROOT, dest, ignore=LEAVE_OUT, dirs_exist_ok=True)
    shutil.copytree(HOUSES / slug / "intake", dest / "01 intake" / slug)
    print(f"Ready: {dest}\nGive the agent: Sam just dropped in a new house, {slug}. Run it through the "
          f"folder and build the request for the difference.\nPlay Sam from {HOUSES / slug / 'sam-answers.md'}")


def latest(folder, stem, ext="md"):
    found = [(int(m.group(1)), p) for p in folder.glob(f"{stem}-*.{ext}")
             if (m := re.match(rf"{stem}-(\d+)\.{ext}$", p.name))]
    return max(found)[1] if found else None


def load(run, slug):
    """The run's own records, the same way the request script loads them."""
    sys.path.insert(0, str(run / "05 request"))
    import money  # noqa: E402  (the run's copy, so a changed gate is scored as it ran)
    paths = {"read-back": latest(run / "02 read" / slug, "read-back"),
             "variance": latest(run / "03 compare" / slug, "variance"),
             "review": latest(run / "04 review" / slug, "review")}
    texts = {k: money.read_text(p) if p else "" for k, p in paths.items()}
    grid = paths["read-back"].with_name(paths["read-back"].name.replace("read-back-", "grid-", 1))         if paths["read-back"] else None
    texts["grid"] = money.read_text(grid) if grid and grid.is_file() else None
    texts["price-list"] = money.prices.snapshot_bytes(slug, texts["read-back"]) if texts["read-back"] else None
    return money, paths, texts


def variance_found(money, text):
    rows = money.section(money.tables(text), "rows")
    return {(money.po_key(money.column(r, "po number")), money.column(r, "item").strip().lower()):
            money.to_amount(money.column(r, "variance")) for r in rows}


def score_rows(h, money, texts, results):
    found = variance_found(money, texts["variance"])
    rows = [r for r in h["rows"] if not r.get("unpriced")]
    for r in rows:
        key = (r["po"], r["item"].lower())
        rate = money.prices.parse(texts["price-list"] or b"")[0].get(r["item"].lower(), {}).get("rate")
        want = (Decimal(r["measured"]) * rate - Decimal(r.get("po_qty", "0")) * Decimal(r.get("po_rate", "0"))
                - Decimal(r.get("epo", "0"))) if rate is not None else None
        results.append((found.get(key) == want, f"variance {r['item']} ({r['po']}): want {want}, got {found.get(key)}"))
    extra = set(found) - {(r["po"], r["item"].lower()) for r in rows}
    results.append((not extra, f"no variance rows beyond the key: {sorted(extra) or 'none'}"))
    total = sum((v for v in found.values() if v is not None), Decimal(0))
    results.append((total == Decimal(h["expected"]["total"]), f"house total: want {h['expected']['total']}, got {total}"))


def score_request(h, run, slug, money, texts, results):
    pdf = latest(run / "05 request" / slug, "vpo-request", "pdf")
    want = h["expected"]["request"]
    if want is None:
        results.append((pdf is None, f"no request numbered: {'none' if pdf is None else pdf.name}"))
        return
    exp, problems = money.expected_request(texts)
    results.append((not problems, f"money gate on the run's records: {problems or 'no problems'}"))
    got = (exp["house"]["before"], exp["house"]["tax"], exp["house"]["total"])
    results.append((got == tuple(Decimal(want[k]) for k in ("before", "tax", "total")),
                    f"request totals: want {want['before']}, {want['tax']}, {want['total']}; got {got}"))
    results.append((pdf is not None, f"request numbered: {pdf.name if pdf else 'none'}"))


def score(slug, run):
    h, run = spec(slug), Path(run)
    money, paths, texts = load(run, slug)
    results = [(paths["read-back"] is not None, "a read-back was written")]
    if texts["read-back"]:
        price_problems = money.prices.check_read_back(texts["read-back"], texts["price-list"])
        results.append((not price_problems, f"price check: {price_problems or 'pass'}"))
        results.append((money.approved(texts["read-back"]), "read-back carries Sam's yes"))
    if texts["variance"]:
        score_rows(h, money, texts, results)
    score_request(h, run, slug, money, texts, results)
    for ok, line in results:
        print(("PASS  " if ok else "FAIL  ") + line)
    passed = all(ok for ok, _ in results)
    print(f"\n{slug}: {'PASS' if passed else 'FAIL'} ({sum(ok for ok, _ in results)} of {len(results)})")
    return passed


def main(argv):
    if len(argv) != 4 or argv[1] not in ("prepare", "score"):
        sys.exit("Use: python tests/cold_run.py prepare|score <house> <folder>")
    if argv[1] == "prepare":
        prepare(argv[2], argv[3])
    else:
        sys.exit(0 if score(argv[2], argv[3]) else 1)


if __name__ == "__main__":
    main(sys.argv)
