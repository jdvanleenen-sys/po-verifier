# PO Verifier

A folder an AI agent runs to check a painting contractor's builder purchase orders (POs) against
what he actually measured on site, then build a one-page request for the difference, with the
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
| `05 request` | A one-page request PDF, checked by a script before it gets a number | the painter says yes, and sends it himself |
| `06 outcome` | What the builder paid against it | the painter confirms |

Two rules never bend: the AI never decides the money, and it never sends anything.

## Test it
Want to break it? See **[TESTING.md](TESTING.md)**. There is a house waiting for you to run.

## Status
- 2 practice houses run cold by a fresh AI with no memory of the build. Every number matched an
  answer key worked out separately, to the cent.
- Not yet run on a real job. That is the next step.
- What changed and why: `change-log.md`.

Built by Jeff Van Leenen (AI the vL Way).
