// On a computer only: the house list in a sidebar with the open house's steps under it, and files
// dragged onto the New house screen. The phone never runs any of this.
"use strict";

const WIDE = window.matchMedia("(min-width: 900px)");
const STEP_NAMES = ["Add files", "Reading", "Check a couple things", "The difference", "Your PDF"];
const STEP_AT = { reading: 1, check: 2, difference: 3, pdf: 4, done: 5, "no-request": 5 };

async function drawSide(current, screen) {
  const side = document.getElementById("side");
  side.hidden = !WIDE.matches;
  if (!WIDE.matches) return;
  let list = [];
  try { list = await api("/api/houses"); } catch (e) { return; }
  const at = STEP_AT[screen] ?? 0;
  const steps = current ? `<div class="small" style="margin-top:8px">${STEP_NAMES.map((n, i) =>
    `<div${i === at ? ' style="font-weight:600;color:var(--ink)"' : ""}>${i < at ? "Done: " : ""}${n}</div>`).join("")}</div>` : "";
  side.innerHTML = `<div class="small">Your houses</div>` + list.map((h) =>
    `<button class="card house${h.house === current ? " cur" : ""}" data-side="${esc(h.house)}"><b>${esc(h.address)}</b>
     <span class="small">${h.busy ? "Working" : esc(h.note || STATUS[h.screen] || h.screen)}</span></button>
     ${h.house === current ? steps : ""}`).join("") + `<button class="btn sec" data-side-new>New house</button>`;
  side.querySelectorAll("[data-side]").forEach((b) => (b.onclick = () => (location.hash = "h/" + b.dataset.side)));
  side.querySelector("[data-side-new]").onclick = () => (location.hash = "new");
}

function wireDrops() {
  document.querySelectorAll(".drop").forEach((zone) => {
    const input = zone.querySelector("input[type=file]");
    zone.ondragover = (e) => { e.preventDefault(); zone.classList.add("over"); };
    zone.ondragleave = () => zone.classList.remove("over");
    zone.ondrop = (e) => {
      e.preventDefault();
      zone.classList.remove("over");
      const merged = new DataTransfer();
      [...input.files, ...e.dataTransfer.files].forEach((f) => merged.items.add(f));
      input.files = merged.files;
    };
  });
}
