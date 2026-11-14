// The Difference screen's taps: on or off per row, the reason when a flagged row comes off, the PO a
// no-PO row's EPO goes on, the notes answer, and the preview total (exact, in cents).
"use strict";

function readPicks(h) {
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

function updateDifference(h) {
  let total = 0;
  for (const card of app.querySelectorAll("[data-row]")) {
    const row = h.rows.find((r) => r.row === card.dataset.row);
    const on = card.querySelector("[data-on].on");
    const isOn = on && on.dataset.on === "1";
    card.querySelector("[data-reason]").hidden = !(on && !isOn && row.default === "on");
    const epo = card.querySelector("[data-epo]");
    if (epo) epo.hidden = !isOn;
    if (isOn) total += cents(row.variance);
  }
  document.getElementById("total").textContent = dollars(total);
}

function wireDifference(h) {
  for (const card of app.querySelectorAll("[data-row]")) {
    card.querySelectorAll("[data-on]").forEach((b) => (b.onclick = () => {
      card.querySelectorAll("[data-on]").forEach((x) => x.classList.toggle("on", x === b));
      updateDifference(h);
    }));
  }
  app.querySelectorAll("[data-notes]").forEach((b) => (b.onclick = () =>
    app.querySelectorAll("[data-notes]").forEach((x) => x.classList.toggle("on", x === b))));
  updateDifference(h);
  const build = app.querySelector("[data-review]");
  build.onclick = () => {
    const notes = app.querySelector("[data-notes].on");
    if (!notes) return showError(new Error("Say whether your site notes go with the request."));
    build.disabled = true;
    act(h, "review", { picks: readPicks(h), notes: notes.dataset.notes }).then(() => (build.disabled = false));
  };
}
