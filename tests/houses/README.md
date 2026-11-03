# Test houses

Nine made-up houses, each built to catch one kind of mistake. Every one has builder POs, Sam's site
notes in his own shorthand, and the answers Sam gives when the folder asks. The answer key is
`houses.json`; `tests/test_houses.py` re-prices it from the price list so a wrong key fails first.

| House | What it tests | Right answer |
|---|---|---|
| `21-clean-court` | Notes match every PO | $0.00 everywhere, no request |
| `5-short-street` | Short counts, a PO at an old rate, a credit back to the builder | $245.00 + $12.25 GST = $257.25 |
| `88-extra-lane` | Work on no PO, 2 doors already paid by EPO (never ask twice) | $525.00 + $26.25 = $551.25 |
| `9-trap-way` | Multi family rate, handrail vs railing, garage on painted area, "2,615" | $120.00 + $6.00 = $126.00 |
| `30-not-listed-road` | Items on no price list row, a note that fits two rows | $56.00 + $2.80 = $58.80 |
| `62-messy-notes-bay` | A recount, a number with no unit, a misspelling, a double touch-up, a back charge | $180.00 + $9.00 = $189.00 |
| `14-photo-notes-close` | Notes as a handwritten phone photo, a crossed-out count, work on no PO | $480.00 + $24.00 = $504.00 |
| `27-voice-memo-way` | Notes as a phone voice-memo transcript: numbers in words, "for" for four, a correction mid-sentence | $405.00 + $20.25 = $425.25 |
| `36-two-photos-lane` | Notes as two photos, one sideways, glare over the railing number | $114.00 + $5.70 = $119.70 |

The last three draw their photos with `handwriting.py` from the text in `houses.json`.

## Run one cold
1. `python tests/cold_run.py prepare <house> <new folder outside this repo>`
2. Open that folder in a fresh agent and give it the line `prepare` prints. No other hints.
3. Play Sam from `tests/houses/<house>/sam-answers.md`, only when asked.
4. `python tests/cold_run.py score <house> <that folder>`. PASS means every row, the total and the
   request match the key.

To change a house, edit `houses.json`, run `python tests/houses/make_houses.py`, then the tests.
