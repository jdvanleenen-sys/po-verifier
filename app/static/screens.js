// The seven screens. Each takes the laptop's answer for the house and draws it; every tap posts one
// action and then redraws from the laptop's new answer, so the phone never holds state of its own.
"use strict";

const STATUS = { reading: "Not read yet", compare: "Working out the difference", check: "Needs your check", difference: "Pick what to chase",
  pdf: "PDF ready to approve", done: "Request approved", "no-request": "Nothing to ask for", stopped: "Stopped" };

function housesScreen(list) {
  const rows = list.map((h) => `<button class="card house" data-go="${esc(h.house)}"><b>${esc(h.address)}</b>
    <span class="small">${h.busy ? (h.screen === "reading" ? "Reading your files" : "Working") : esc(STATUS[h.screen] || h.screen)}</span></button>`).join("");
  return `<h2>Your houses</h2>${rows || `<p class="sub">No houses yet.</p>`}<button class="btn" data-new>New house</button>`;
}

function newHouseScreen() {
  const today = new Date().toLocaleDateString("en-CA");
  return `<h2>New house</h2>
    <label>Address<input type="text" id="address" autocomplete="off" placeholder="House number and street"></label>
    <div class="card"><b>POs</b><span class="small">PDF, saved page, photo or screenshot</span>
      <input type="file" id="pos" multiple accept=".pdf,.html,.htm,image/*"></div>
    <div class="card"><b>Your notes</b><span class="small">Photo of your notes, or a PDF or text file</span>
      <input type="file" id="notes" multiple accept="image/*,.pdf,.txt"></div>
    <div class="card"><div class="row"><span>The notes page shows other houses too</span><input type="checkbox" id="covers"></div>
      <label>Date measured<input type="date" id="measured" value="${today}" max="${today}"></label>
      <div class="row"><span>Not recorded</span><input type="checkbox" id="norecord"></div></div>
    <div id="ask"></div><p id="err" class="error"></p>
    <button class="btn" id="lock">Lock these files and read them</button>`;
}

function readingScreen(h) {
  if (h.busy) return waiting("Reading your files", h.job, "Usually 3 to 4 minutes. You can lock the phone.");
  const job = h.job || {};
  const why = job.status === "interrupted" ? "The laptop restarted while reading." : job.line || "The read did not finish.";
  return `<h2>The read stopped</h2>${stoppedCard(why)}<button class="btn" data-act="retry">Read again</button>`;
}

function cardHtml(c, i) {
  const head = `<b>${esc(c.title)}</b>${c.po ? `<span class="small">PO ${esc(c.po)}</span>` : ""}`;
  if (c.kind === "warning") {
    return `<div class="card warn" data-card="${i}">${head}<span class="small">Not on your price list. ${esc(c.detail)}</span>
      ${c.closest ? `<span class="small">Closest: ${esc(c.closest)}</span>` : ""}
      <div class="chips"><button class="chip" data-choice="leave">Leave it unpriced</button><button class="chip" data-choice="names">It is this item</button></div>
      <input type="text" data-words placeholder="Price list item, as your list names it" hidden>
      <span class="small">New item for your list? Add it in Excel first, then call for help.</span></div>`;
  }
  if (c.kind === "pick") {
    const opts = c.options.map((o, n) => `<button class="chip" data-choice="${n}">${esc(o)}</button>`).join("");
    return `<div class="card warn" data-card="${i}">${head}<span class="small">This fits two items. Which is it?</span><div class="chips">${opts}</div></div>`;
  }
  if (c.kind === "number") {
    return `<div class="card warn" data-card="${i}">${head}<span class="small">Read as: ${esc(c.read)}. PO says ${esc(c.po_qty)}.</span>
      <span class="small">${esc(c.why)}</span>
      <div class="chips"><button class="chip" data-choice="right">Right</button><button class="chip" data-choice="fix">Fix it</button></div>
      <input type="text" data-words placeholder="What you measured" hidden></div>`;
  }
  return `<div class="card warn" data-card="${i}">${head}<span class="small">${esc(c.why)}</span>
    <textarea data-words rows="2" placeholder="Your answer"></textarea></div>`;
}

function checkScreen(h) {
  if (h.busy) return waiting("Updating what I read", h.job, "Usually 3 to 4 minutes.");
  const photo = h.photos ? `<a href="/api/house/${esc(h.house)}/notes/0" target="_blank"><img class="photo" src="/api/house/${esc(h.house)}/notes/0" alt="Your notes"></a>` : "";
  const rows = h.rows.map((r) => `<div class="row small"><span>${esc(r.line || r.item)}</span><span>${esc((r.measured || "").split(";")[0])}</span></div>`).join("");
  const read = `<details class="card soft"><summary>${h.rows.length} lines read</summary>${rows}</details>`;
  if (h.cards.length) {
    return `<h2>${h.cards.length} thing${h.cards.length > 1 ? "s" : ""} to check</h2>${photo}${h.cards.map(cardHtml).join("")}${read}
      <p id="err" class="error"></p><button class="btn" data-send>Send my answers</button>`;
  }
  if (!h.ready) return `<h2>Check what I read</h2>${stoppedCard(h.blocked)}${read}`;
  return `<h2>Everything is answered</h2><p class="sub">Look over what was read. Your yes covers all of it.</p>${photo}${read}
    <p id="err" class="error"></p><button class="btn" data-act="yes">That's all right</button>`;
}

function diffRow(r) {
  const sign = cents(r.variance) < 0 ? "minus" : "plus";
  const unset = r.default === null;
  const epo = r.epo_asks ? `<label data-epo hidden>Its EPO goes on<select><option value="">Choose</option>
      <option value="__own">Its own No PO group</option>${(window.HOUSE_POS || []).map((p) => `<option>${esc(p)}</option>`).join("")}</select></label>` : "";
  return `<div class="card" data-row="${esc(r.row)}"><div class="row"><b>${esc(r.item)}</b><span class="money ${sign}">${esc(r.variance)}</span></div>
    <span class="small">${r.no_po ? "No PO" : "PO " + esc(r.po)} · ${esc(r.why)} · ${esc(r.call)}${unset ? " · needs your call" : ""}</span>
    <div class="chips"><button class="chip${r.default === "on" ? " on" : ""}" data-on="1">On the PDF</button><button class="chip${r.default === "off" ? " on" : ""}" data-on="0">Leave off</button></div>
    <input type="text" data-reason placeholder="Why it comes off (a few words)" hidden>${epo}</div>`;
}

function differenceScreen(h) {
  window.HOUSE_POS = h.pos;
  const notes = h.shared_notes
    ? `<div class="card"><b>Your notes page shows other houses too.</b><span class="small">Send it to the builder with those houses on it?</span>
       <div class="chips"><button class="chip" data-notes="yes-other-house">Yes, send it</button><button class="chip" data-notes="no">No</button></div></div>`
    : `<div class="card"><b>Attach your site notes as proof?</b><div class="chips"><button class="chip" data-notes="yes">Yes</button><button class="chip" data-notes="no">No</button></div></div>`;
  return `<h2>${h.rows.length} line${h.rows.length === 1 ? "" : "s"} differ</h2><p class="sub">From your price list. You pick what goes on the PDF.</p>
    ${h.rows.map(diffRow).join("")}<div class="card"><div class="row"><span>On the PDF, before tax (preview)</span><span class="money" id="total"></span></div></div>
    ${notes}<p id="err" class="error"></p><button class="btn" data-review>Build the PDF</button>`;
}

function pdfScreen(h) {
  if (h.busy) return waiting("Building your PDF", h.job, "Usually 2 to 4 minutes.");
  const lines = h.checks.map((l) => `<div class="check-line${/:\s*fail:/i.test(l) ? " fail" : ""}">${esc(l).replace(/:\s*(pass|fail):/i, ": <b>$1</b>:")}</div>`).join("");
  if (!h.has_pdf || !h.passed) {
    return `<h2>Your PDF</h2>${stoppedCard(h.has_pdf ? "One of the six checks did not pass." : (h.job && h.job.line) || "The PDF was not built.")}
      <div class="card soft">${lines}</div><button class="btn" data-act="retry">Build it again</button>`;
  }
  return `<h2>Your PDF</h2><a class="btn sec" href="/api/house/${esc(h.house)}/pdf" target="_blank">Open the PDF</a>
    <div class="card ok"><b>All six checks pass</b>${lines}</div>
    <p class="sub">Notes attached: ${h.notes === "no" ? "no" : "yes"}.</p><p id="err" class="error"></p>
    <button class="btn go" data-act="approve">Approve</button>`;
}

function doneScreen(h) {
  if (h.screen === "no-request") return `<h2>Nothing to ask for</h2><p class="sub">Your yes is on record. This house needs no request.</p>`;
  return `<div class="card ok"><b>Approved</b><span class="small">${esc(h.approved)} · ${esc(h.document)}</span></div>
    <p class="sub">Send it to the site super yourself. The app never sends anything.</p>
    <button class="btn" data-share>Save or share the PDF</button>
    ${h.sent ? `<p class="sub">Marked as sent.</p>` : `<button class="btn sec" data-act="sent">I sent it</button>`}`;
}
