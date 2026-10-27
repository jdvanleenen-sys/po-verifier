# PO Verifier

*Agents: start at `CLAUDE.md`. This page and `_for-testers/` are for people.*

A folder an AI agent runs to check a painting contractor's builder purchase orders (POs) against
what he actually measured on site, then build a request for the difference, with the
proof attached.

**It is a practice build with made-up data.** The builder, the painter, the addresses, the POs
and the rates are all stand-ins. Nothing in it sends anything to anyone.

## Why it exists
A painter who works for home builders is paid through the builders' POs. The POs are often wrong
(the wrong rate, too few doors, items never used), and nobody checks them. The painter does it
at night after a 12-hour day, or not at all, so money goes unbilled. This folder does the
checking, shows every number, and leaves every decision to the painter.

## How it works
It is an ICM workspace (Interpretable Context Methodology, Jake Van Clief and David McDermott's
method): the folders are the agent's instructions. `CLAUDE.md` is the agent's front door, and
`CONTEXT.md` is the map. A house moves through 6 stages:

| Stage | What happens | Who decides |
|---|---|---|
| `01 intake` | The POs and the painter's notes arrive, untouched | |
| `02 read` | The documents turned into rows | the painter says yes |
| `03 compare` | The difference, line by line, by calculation | runs on its own |
| `04 review` | What is worth chasing | the painter decides |
| `05 request` | A request PDF with the proof attached. A script works every dollar out again from the painter's approved records and runs all six checks on the PDF before it gets a number | the painter says yes, and sends it himself |
| `06 outcome` | What the builder paid against it | the painter confirms |

Two rules never bend: the AI never decides the money, and it never sends anything.

## Test it
Want to break it? See **[_for-testers/TESTING.md](_for-testers/TESTING.md)**. There is a house waiting for you to run.

## Status
- The finished example, 77 Mockup Drive, checks out to the cent: `python -m unittest discover -s tests`
  re-adds it and plants 13 mistakes the money gate must refuse.
- The test house, 14 Example Crescent, has been run cold by a fresh AI twice (2026-10-25 and
  2026-10-27; those runs are not in the repo). Both matched its sealed answer key to the cent.
  Yours is the next run.
- Not yet run on a real job. That is the next step.
- What changed and why: `change-log.md`.

Built by Jeff Van Leenen (AI the vL Way).
