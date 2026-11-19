// The Difference screen's taps: on or off per row, the reason when a flagged row comes off, the PO a
// no-PO row's EPO goes on, the notes answer, and the preview total (exact, in cents). Build the PDF
// stays off until every row with no default has a call, every chosen no-PO row has its PO, and the
// notes question is answered; the laptop checks all of it again.
"use strict";

function readPicks() {
  const picks = {};
  for (const card of app.querySelectorAll("[data-row]")) {
    const on = card.querySelector("[data-on].on");
    if (!on) continue;
    const pick = { on: on.dataset.on === "1", reason: card.querySelector("[data-reason]").value };
    const select = card.querySelector("[data-epo] select");
    if (select && select.value) pick.epo = select.value === "__own" ? "" : select.value;
    picks[card.dataset.row] = pick;
  }
  return picks;
}

function missing(h) {
  for (const card of app.querySelectorAll("[data-row]")) {
    const row = h.rows.find((r) => r.row === card.dataset.row);
    const on = card.querySelector("[data-on].on");
    if (!on) return `${row.item}: on the PDF or leave off?`;
    const select = card.querySelector("[data-epo] select");
    if (on.dataset.on === "1" && select && !select.value) return `${row.item}: which PO does its EPO go on?`;
  }
  const anyOn = [...app.querySelectorAll("[data-on].on")].some((b) => b.dataset.on === "1");
  if (anyOn && !app.querySelector("[data-notes].on")) return "Say whether your site notes go with the request.";
  if (!anyOn && !app.querySelector("[data-none-reason]").value.trim()) return "Say in a few words why nothing goes on.";
  return "";
}

function updateDifference(h) {
  let total = 0, anyOn = false;
  for (const card of app.querySelectorAll("[data-row]")) {
    const row = h.rows.find((r) => r.row === card.dataset.row);
    const on = card.querySelector("[data-on].on");
    const isOn = on && on.dataset.on === "1";
    card.querySelector("[data-reason]").hidden = !(on && !isOn && row.default === "on");
    const epo = card.querySelector("[data-epo]");
    if (epo) epo.hidden = !isOn;
    if (isOn) { total += cents(row.variance); anyOn = true; }
  }
  document.getElementById("total").textContent = dollars(total);
  app.querySelector("[data-none-reason]").hidden = anyOn || !h.rows.length;
  const build = app.querySelector("[data-review]");
  const gap = missing(h);
  build.disabled = Boolean(gap);
  build.title = gap;
  document.getElementById("gap").textContent = gap ? "Still to answer: " + gap : "";
  build.textContent = anyOn ? "Build the PDF" : "Nothing to ask for: save my answer";
}

function wireDifference(h) {
  for (const card of app.querySelectorAll("[data-row]")) {
    card.querySelectorAll("[data-on]").forEach((b) => (b.onclick = () => {
      card.querySelectorAll("[data-on]").forEach((x) => x.classList.toggle("on", x === b));
      updateDifference(h);
    }));
    const select = card.querySelector("[data-epo] select");
    if (select) select.onchange = () => updateDifference(h);
  }
  app.querySelectorAll("[data-notes]").forEach((b) => (b.onclick = () => {
    app.querySelectorAll("[data-notes]").forEach((x) => x.classList.toggle("on", x === b));
    updateDifference(h);
  }));
  const noneReason = app.querySelector("[data-none-reason]");
  noneReason.oninput = () => updateDifference(h);
  updateDifference(h);
  const build = app.querySelector("[data-review]");
  build.onclick = () => {
    const notes = app.querySelector("[data-notes].on");
    build.disabled = true;
    act(h, "review", { picks: readPicks(), notes: notes ? notes.dataset.notes : null, none_reason: noneReason.value })
      .then(() => { if (app.querySelector("[data-review]")) updateDifference(h); });
  };
}
