"""Loop run 2 attacks, 2026-11-09: header facts and the record chain. Run from the repo root:

    python -m unittest discover -s tests -v

On a real house the request printed a date Sam never gave (a07), another community (a08) and a
builder cut to "Homes" (a09), and all six checks passed. A review whose from: named another house's
variance passed (a31), and "EPO goes on" with a typo ("/0943") was read as /094 (a36).
"""
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "05 request"), str(ROOT / "02 read")]
import chain  # noqa: E402
import header_checks  # noqa: E402
import house_checks  # noqa: E402
import money  # noqa: E402
import verify  # noqa: E402

PDF = ROOT / "05 request" / "77-mockup-drive" / "vpo-request-1.pdf"
SPEC = {"document": "VR-0001", "job_numbers": ["77", "24", "3"], "job_names": ["MKR-02402401-77 Mockup Drive"],
        "measured": "2026-10-02", "builders": "Sample Builder Ltd., through SupplyPro",
        "po_builder": "Sample Builder Ltd.", "community": "Mockup Ridge Single Family", "review_date": "2026-10-14"}


def head(old=None, new=None):
    pages = verify.split_request(verify.pdf_pages(PDF))[0]
    if old:
        assert old in pages[0], old
        pages = [pages[0].replace(old, new, 1)] + pages[1:]
    return pages


def problems(pages, **spec):
    return header_checks.header_problems(pages, dict(SPEC, **spec))


class HeaderFacts(unittest.TestCase):
    def test_sample_passes_with_every_fact_known(self):
        self.assertEqual(problems(head()), [])

    def test_a07_a_date_printed_when_house_info_gives_none_is_refused(self):
        self.assertTrue(problems(head(), measured=None))

    def test_a07_not_recorded_passes_when_house_info_gives_none(self):
        self.assertEqual(problems(head("October 2, 2026", "Date not recorded"), measured=None), [])

    def test_a08_another_community_is_refused(self):
        found = problems(head("Mockup Ridge Single Family", "Other Ridge Single Family"))
        self.assertTrue(any("community" in p for p in found), found)

    def test_a09_part_of_the_builder_name_is_refused(self):
        found = problems(head("Sample Builder Ltd.", "Ltd."))
        self.assertTrue(any("builder" in p for p in found), found)

    def test_named_builders_are_whole_names(self):
        self.assertEqual(header_checks.named_builders("A Homes; B Ltd., through SupplyPro"), ["a homes", "b ltd."])
        self.assertEqual(header_checks.named_builders("C Homes, POs from the builder's system"),
                         ["c homes"])

    def test_prepared_before_sams_yes_is_refused(self):
        self.assertTrue(problems(head(), review_date="2026-10-20"))

    def test_prepared_in_the_future_is_refused(self):
        later = date.today() + timedelta(days=3)
        found = problems(head("October 17, 2026", f"{later:%B} {later.day}, {later.year}"))
        self.assertTrue(any("prepared" in p for p in found), found)

    def test_header_extras_read_the_po_from_line(self):
        texts = ["FROM: Sample Builder Ltd. - Mockup Ridge Single Family ADDRESS: x"] * 2
        got = house_checks.header_extras(texts, "- Date: 2026-10-14\n")
        self.assertEqual(got, {"po_builder": "Sample Builder Ltd.", "community": "Mockup Ridge Single Family",
                               "review_date": "2026-10-14"})

    def test_header_extras_skip_when_pos_disagree(self):
        texts = ["FROM: A - One ADDRESS: x", "FROM: A - Two ADDRESS: x"]
        self.assertIsNone(house_checks.header_extras(texts, "")["community"])


class RecordChain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for house in ("12-sample-road", "14-other-road"):
            (self.root / "03 compare" / house).mkdir(parents=True)
            (self.root / "03 compare" / house / "variance-1.md").write_text("x", encoding="utf-8")
        (self.root / "04 review" / "12-sample-road").mkdir(parents=True)
        self.review = self.root / "04 review" / "12-sample-road" / "review-1.md"

    def tearDown(self):
        self.tmp.cleanup()

    def chain(self, origin):
        return chain.chain_problems(self.review, f"attempt: 1\nfrom: {origin}\n", self.root)

    def test_own_house_passes(self):
        self.assertEqual(self.chain("03 compare/12-sample-road/variance-1.md"), [])

    def test_a31_another_house_is_refused(self):
        found = self.chain("03 compare/14-other-road/variance-1.md")
        self.assertTrue(any("not this house" in p for p in found), found)

    def test_a_later_stage_is_refused(self):
        (self.root / "05 request" / "12-sample-road").mkdir(parents=True)
        (self.root / "05 request" / "12-sample-road" / "x.md").write_text("x", encoding="utf-8")
        self.assertTrue(self.chain("05 request/12-sample-road/x.md"))


class EpoGoesOnExactly(unittest.TestCase):
    REVIEW = """| Row | PO number | Item | Variance | Call | Sam's decision (on / off) | Reason | EPO goes on |
|---|---|---|---|---|---|---|---|
| 13 | none | Mantle | +$240.00 | flag | on | | {target} |
"""

    def targets(self, target):
        found = []
        chosen = {("none", "mantle", "13"): True}
        got = money.epo_targets(self.REVIEW.format(target=target), chosen, {"SMP-0101/094", "SMP-0101/093"}, found)
        return got, found

    def test_exact_po_passes(self):
        got, found = self.targets("SMP-0101/094")
        self.assertEqual((got, found), ({("none", "mantle", "13"): "SMP-0101/094"}, []))

    def test_a36_a_typo_is_refused(self):
        got, found = self.targets("SMP-0101/0943")
        self.assertEqual(got, {})
        self.assertTrue(found and "not a PO in this house" in found[0], found)


if __name__ == "__main__":
    unittest.main()
