# My page (a painting contractor's purchase orders)

Made-up data, real problem. The builder, the painter, the addresses, the POs and the rates are all
stand-ins.

## Who receives it
A painting contractor who works for home builders and is paid through the builder's purchase
orders.

## The line
For trade contractors, we fix one office bottleneck (missed calls, slow estimates, late invoices,
or scattered job details) with the simplest system that works, one their team can run, check, and
change, so fewer jobs, dollars, and evenings slip through the cracks.

For this build, the bottleneck is wrong purchase orders: I turn his purchase orders and his real
measurements into a document that shows the differences, so he gets paid for the work he has done,
on both sides.

## The steps
1. Find the pain. Sit with the contractor and ask where the paperwork costs him money (judgment)
2. The builder's POs arrive through the builder's ordering system, often several per house (rule)
3. Look up the agreed rate on the current price list (lookup)
4. Measure on site: handrail feet, doors, stringer caps (rule)
5. Compare the POs against the price list and his measurements, line by line (lookup) **circled**
6. Decide what is worth chasing. Small differences are ignored, large ones flagged, the ones in
   between are his call (judgment) **AI never does this**
7. Request an added PO from the builder, with the proof attached. Never delete a PO (rule)
8. Build the invoice on the checked totals (rule)
9. He checks every dollar and sends it (judgment) **AI never does this**

## The circled step
Step 5. Today he does it at night after a 12-hour day, or not at all, so money goes unbilled.

## The steps AI must never do
Steps 6 and 9. The AI never decides the money and never sends anything. Every amount is worked
out by a formula, and he approves anything that goes to a builder.

## Inputs
For each house, the builder's POs and EPOs and the painter's site measurements, dropped into
`01 intake/<house>/`. The price list in Airtable, as described in `reference/price-list.md`.

## Done, in his words
Not asked yet in his words. My read so far: a document he can keep that shows the difference
between the purchase orders and his real measurements, on both sides.
