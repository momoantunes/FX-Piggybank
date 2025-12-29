const PAIRS = {
  usd: { label: "🇺🇸 USD/BRL", file: "./data/usdbrl.json", btnId: "btnUSD" },
  eur: { label: "🇪🇺 EUR/BRL", file: "./data/eurbrl.json", btnId: "btnEUR" },
};

function fmtBRL(n) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n);
}

function fmtPct(n) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function percentChange(current, previous) {
  if (previous == null || previous === 0) return null;
  return ((current - previous) / previous) * 100;
}

async function loadHistory(file) {
  const res = await fetch(file, { cache: "no-store" });
  if (!res.ok) throw new Error(`Falha ao carregar ${file}: ${res.status}`);
  return await res.json();
}

function drawLineChart(canvas, points) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (points.length < 2) {
    ctx.fillText("Sem dados suficientes.", 20, 40);
    return;
  }

  const pad = 30;
  const W = canvas.width, H = canvas.height;
  const ys = points.map(p => p.bid);

  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const rangeY = (maxY - minY) || 1;

  const xTo = (i) => pad + (i / (ys.length - 1)) * (W - pad * 2);
  const yTo = (v) => (H - pad) - ((v - minY) / rangeY) * (H - pad * 2);

  ctx.globalAlpha = 0.6;
  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, H - pad);
  ctx.lineTo(W - pad, H - pad);
  ctx.stroke();
  ctx.globalAlpha = 1;

  ctx.beginPath();
  ctx.moveTo(xTo(0), yTo(ys[0]));
  for (let i = 1; i < ys.length; i++) ctx.lineTo(xTo(i), yTo(ys[i]));
  ctx.stroke();

  ctx.fillText(`min ${minY.toFixed(4)}`, pad, pad - 10);
  ctx.fillText(`max ${maxY.toFixed(4)}`, pad + 120, pad - 10);
}

function getSelectedKey() {
  const url = new URL(window.location.href);
  const qs = (url.searchParams.get("pair") || "").toLowerCase();
  if (qs && PAIRS[qs]) return qs;

  const saved = (localStorage.getItem("fx_pair") || "").toLowerCase();
  if (saved && PAIRS[saved]) return saved;

  return "usd";
}

function setSelectedKey(key) {
  localStorage.setItem("fx_pair", key);
  const url = new URL(window.location.href);
  url.searchParams.set("pair", key);
  history.replaceState({}, "", url.toString());
}

function setActiveButton(key) {
  for (const k of Object.keys(PAIRS)) {
    const btn = document.getElementById(PAIRS[k].btnId);
    if (!btn) continue;
    btn.classList.toggle("active", k === key);
  }
}

async function render(key) {
  const conf = PAIRS[key];
  setActiveButton(key);

  const history = await loadHistory(conf.file);

  if (!Array.isArray(history) || history.length === 0) {
    document.getElementById("lastBid").textContent = "Sem dados ainda";
    document.getElementById("lastMeta").textContent = "";
    document.getElementById("delta").textContent = "—";
    document.getElementById("deltaMeta").textContent = "";
    document.getElementById("source").textContent = "—";
    return;
  }

  const last = history[history.length - 1];
  const prev = history.length >= 2 ? history[history.length - 2] : null;

  const lastBid = Number(last.bid);
  const prevBid = prev ? Number(prev.bid) : null;

  document.getElementById("lastBid").textContent = fmtBRL(lastBid);
  document.getElementById("lastMeta").textContent = `UTC: ${last.timestamp_iso}`;

  const chg = percentChange(lastBid, prevBid);
  document.getElementById("delta").textContent = chg == null ? "N/A" : fmtPct(chg);
  document.getElementById("deltaMeta").textContent = prev ? `Anterior UTC: ${prev.timestamp_iso}` : "Sem ponto anterior";

  document.getElementById("source").textContent = last.source || "—";

  const slice = history.slice(-60).map(x => ({ bid: Number(x.bid) }));
  drawLineChart(document.getElementById("chart"), slice);
  document.getElementById("chartMeta").textContent = `${conf.label} • mostrando ${slice.length} pontos`;
}

(function main() {
  const key = getSelectedKey();
  setSelectedKey(key); // garante URL coerente
  render(key).catch(err => console.error(err));

  document.getElementById("btnUSD").addEventListener("click", () => {
    setSelectedKey("usd");
    render("usd").catch(err => console.error(err));
  });

  document.getElementById("btnEUR").addEventListener("click", () => {
    setSelectedKey("eur");
    render("eur").catch(err => console.error(err));
  });
})();
