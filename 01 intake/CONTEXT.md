# 01 intake: what arrives for a house

## What this stage is for
Everything about one house lands here first, exactly as Sam received it.

## What comes in
- The builder's POs for the house.
- Any EPOs the builder has already issued for it. An EPO (extra purchase order) and a VPO
  (variance purchase order) are the same document: Sam asks for one, and the builder issues it.
- Sam's measurements from site.

## Who puts it here, and how
Sam. The builder sends him the PO, or he retrieves it from SupplyPro. He takes his measurements
on site. Then he puts the PO and the measurements into the PO Verifier: he drags the files in, or
takes a photo with his phone in the Claude app. After that he should see the results.

## What Sam includes with it
- The address of the house.
- The lot number.
- The builder's name.
- The date he measured.
- The date he dropped the files in.

`house-info.md` has a line for each, `- Date measured: <YYYY-MM-DD>` included; leave a line blank
rather than leaving it out. The folder is named for the address, or a nickname (`real-2`) when the
address must stay private; the nickname is used in every stage.

## How it is filed
One folder per house, named for the address, such as `77-mockup-drive`.

## What is checked here
1. The address, the date measured and the date dropped in are there.
2. There is at least one PO and one set of measurements.
3. Every PO and EPO shows its PO number.

If any of these is missing, ask Sam. Nothing moves on until all three pass, with two exceptions:
- **No date measured, and Sam says there is none** ("move past it"): write `- Date measured: not
  recorded (Sam, <date he said it>)` in the read-back's house section and go on. The request prints
  "Date not recorded". That is Sam's waiver, not a pass.
- **No lot or builder from Sam:** never ask. Take them from the POs when every PO prints the same
  lot and builder; the request prints the POs' lot. Ask only when the POs disagree.

**When the notes page covers two houses,** write so in `house-info.md` ("It covers two houses"); the
request then needs Sam's yes in those words before the page goes to the builder.

**A document that arrives after the first read** never goes into this house's intake: intake
never changes once a house is read, and the scripts refuse a file added later. Take it out and ask
Sam. A document that belongs to this house and came late starts a new house folder, `<house>-2`.

## What goes out
The same files, untouched, ready for the read stage (`../02 read/`).

## What must never happen here
- After the files are dropped in, nothing writes to `house-info.md`, not even Sam's own
  corrections ("the room is 12' x 12', so 384, not 392"; "no date, move past it"). His answers go in
  the read-back's house section and rows, where his yes covers them. Found by a tester, 2026-11-07:
  the agent had written Sam's correction into intake. Intake is fingerprinted from the first read, so
  an edit before that is caught only by this rule.
Nothing that arrives is edited, renamed or deleted. Nothing is read into numbers here. That is
the next stage's job.

## Open
How a photo taken on Sam's phone gets from the Claude app into this folder is not decided.
