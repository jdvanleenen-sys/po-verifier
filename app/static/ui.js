// Small helpers shared by every screen: talking to the laptop, writing safe HTML, and the waiting view.
"use strict";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, { credentials: "same-origin", ...options });
  } catch (e) {
    throw new Error("The phone cannot reach the laptop. Check both are on the same Wi-Fi, then try again.");
  }
  const text = await response.text();
  let data = {};
  try { data = text ? JSON.parse(text) : {}; } catch (e) { data = { error: text }; }
  if (!response.ok) throw new Error(data.error || text || `The laptop answered ${response.status}.`);
  return data;
}

const post = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });

function minutes(seconds) {
  const m = Math.floor((seconds || 0) / 60), s = (seconds || 0) % 60;
  return m ? `${m} min ${s} s` : `${s} s`;
}

function cents(cell) {
  const m = String(cell || "").replace(/[$,+\s]/g, "").match(/^(-?)(\d+)(?:\.(\d{1,2}))?$/);
  if (!m) return 0;
  return (m[1] ? -1 : 1) * (Number(m[2]) * 100 + Number((m[3] || "0").padEnd(2, "0")));
}

function dollars(c) {
  const sign = c < 0 ? "-" : c > 0 ? "+" : "";
  const abs = Math.abs(c);
  return `${sign}$${Math.floor(abs / 100).toLocaleString("en-CA")}.${String(abs % 100).padStart(2, "0")}`;
}

function waiting(title, job, note, limit) {
  const long = job && job.long;
  return `<h2>${esc(title)}</h2><p class="sub">${esc(note)}</p>
    <div class="card soft"><div class="prog"><span class="spin"></span>Working: ${esc(minutes(job && job.elapsed))} so far</div>
    <div class="small">Your files are locked; nothing can change them now.</div></div>
    ${long ? `<p class="sub">This is taking longer than usual. It stops by itself at ${esc(limit || 30)} minutes, and the house stays at its last good step.</p>
      <button class="btn sec" data-act="keep">Keep waiting</button><button class="btn sec" data-act="stop">Stop</button>` : ""}`;
}

function stoppedCard(text) {
  return `<div class="card bad"><b>Stopped before the money</b><div>${esc(text)}</div>
    <div class="small">Nothing was approved or numbered. If this does not make sense, call for help.</div></div>`;
}
