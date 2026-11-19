// Routing, polling and the taps. Screens come from screens.js; the laptop decides which one shows.
"use strict";

const app = document.getElementById("app");
const STEP = { reading: 1, check: 2, difference: 3, pdf: 4, done: 4, "no-request": 4 };
let timer = null;

function chrome(title, step, back) {
  document.getElementById("title").textContent = title;
  document.getElementById("back").hidden = !back;
  const bar = document.getElementById("steps");
  bar.hidden = !step;
  [...bar.children].forEach((s, i) => s.classList.toggle("on", i < (step || 0)));
}

function showError(err) {
  const box = document.getElementById("err");
  if (box) box.textContent = err.message; else app.insertAdjacentHTML("afterbegin", `<p class="error">${esc(err.message)}</p>`);
}

async function route() {
  clearTimeout(timer);
  const hash = location.hash.slice(1);
  try {
    if (hash === "new") return drawNew();
    if (hash.startsWith("h/")) return drawHouse(decodeURIComponent(hash.slice(2)));
    chrome("PO Checker", 0, false);
    drawSide(null, null);
    app.innerHTML = housesScreen(await api("/api/houses"));
    app.querySelectorAll("[data-go]").forEach((b) => (b.onclick = () => (location.hash = "h/" + b.dataset.go)));
    app.querySelector("[data-new]").onclick = () => (location.hash = "new");
  } catch (err) {
    app.innerHTML = `<p class="error">${esc(err.message)}</p><button class="btn sec" onclick="route()">Try again</button>`;
  }
}

function drawNew() {
  chrome("New house", 1, true);
  drawSide(null, null);
  app.innerHTML = newHouseScreen();
  wireDrops();
  const lockBtn = document.getElementById("lock");
  lockBtn.onclick = async () => {
    const form = new FormData();
    form.append("address", document.getElementById("address").value);
    form.append("measured", document.getElementById("norecord").checked ? "not recorded" : document.getElementById("measured").value);
    form.append("covers", document.getElementById("covers").checked ? "yes" : "no");
    for (const f of document.getElementById("pos").files) form.append("pos", f);
    for (const f of document.getElementById("notes").files) form.append("notes", f);
    lockBtn.disabled = true; lockBtn.textContent = "Uploading";
    try {
      const held = await api("/api/hold", { method: "POST", body: form, credentials: "same-origin" });
      if (!held.questions.length) return lockHouse(held.id, {});
      const q = held.questions[0];
      document.getElementById("ask").innerHTML = `<div class="card warn"><b>${esc(q.ask)}</b><div class="chips">
        <button class="chip" data-a="yes">Yes</button><button class="chip" data-a="no">No</button></div></div>`;
      document.querySelectorAll("[data-a]").forEach((b) => (b.onclick = () => lockHouse(held.id, { [q.id]: b.dataset.a })));
      lockBtn.hidden = true;
    } catch (err) { showError(err); lockBtn.disabled = false; lockBtn.textContent = "Lock these files and read them"; }
  };
}

async function lockHouse(id, answers) {
  try {
    const done = await post("/api/lock", { id, answers });
    location.hash = "h/" + done.house;
  } catch (err) { showError(err); }
}

async function drawHouse(house) {
  const h = await api(`/api/house/${encodeURIComponent(house)}`);
  chrome(h.address, STEP[h.screen], true);
  drawSide(house, h.screen);
  const draw = { reading: readingScreen, check: checkScreen, difference: differenceScreen, pdf: pdfScreen,
    done: doneScreen, "no-request": doneScreen, stopped: stoppedScreen }[h.screen];
  app.innerHTML = draw ? draw(h) : `<p class="sub">Nothing to do here.</p>`;
  wire(h);
  if (h.busy) timer = setTimeout(route, 3000);
}

async function act(h, action, body) {
  try {
    await post(`/api/house/${encodeURIComponent(h.house)}/${action}`, body);
    route();
  } catch (err) { showError(err); }
}

function wire(h) {
  app.querySelectorAll("[data-act]").forEach((b) => (b.onclick = () => {
    if (b.dataset.act === "keep") return route();
    b.disabled = true;
    act(h, b.dataset.act);
  }));
  if (h.screen === "check" && h.cards) wireCards(h);
  if (h.screen === "difference") wireDifference(h);
  app.querySelectorAll("[data-go-home]").forEach((b) => (b.onclick = () => (location.hash = "")));
  app.querySelectorAll("[data-go-new]").forEach((b) => (b.onclick = () => (location.hash = "new")));
  const share = app.querySelector("[data-share]");
  if (share) share.onclick = () => sharePdf(h);
}

function choose(card, button) {
  card.querySelectorAll("[data-choice]").forEach((c) => c.classList.toggle("on", c === button));
  const words = card.querySelector("[data-words]");
  if (words && words.tagName === "INPUT") words.hidden = !["names", "fix"].includes(button.dataset.choice);
}

function wireCards(h) {
  app.querySelectorAll("[data-card]").forEach((card) =>
    card.querySelectorAll("[data-choice]").forEach((b) => (b.onclick = () => choose(card, b))));
  const send = app.querySelector("[data-send]");
  if (!send) return;
  send.onclick = () => {
    const answers = {};
    app.querySelectorAll("[data-card]").forEach((card) => {
      const c = h.cards[Number(card.dataset.card)];
      const on = card.querySelector("[data-choice].on");
      const words = card.querySelector("[data-words]");
      answers[c.id] = { choice: on ? on.dataset.choice : "", words: words ? words.value : "" };
    });
    send.disabled = true;
    act(h, "answers", { answers }).then(() => (send.disabled = false));
  };
}

async function sharePdf(h) {
  const url = `/api/house/${encodeURIComponent(h.house)}/pdf?numbered=1`;
  try {
    const blob = await (await fetch(url, { credentials: "same-origin" })).blob();
    const file = new File([blob], `${h.document}.pdf`, { type: "application/pdf" });
    if (navigator.canShare && navigator.canShare({ files: [file] })) return await navigator.share({ files: [file], title: h.document });
  } catch (err) { if (err.name === "AbortError") return; }
  window.open(url, "_blank");
}

window.addEventListener("hashchange", route);
document.getElementById("back").onclick = () => (location.hash = "");
route();
