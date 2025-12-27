async function loadHistory() {
  const res = await fetch("./data/usdbrl.json", { cache: "no-store" });
  if (!res.ok) throw new Error(`Falha ao carregar histórico: ${res.status}`);
  return await res.json();
}

function fmtBRL(n) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n);
}

function fmtPct(n) {
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
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
  const xs = points.map((_, i) => i);
  const ys = points.map(p => p.bid);

  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const rangeY = (maxY - minY) || 1;

  const xTo = (i) => pad + (i / (xs.length - 1)) * (W - pad * 2);
  const yTo = (v) => (H - pad) - ((v - minY) / rangeY) * (H - pad * 2);

  // eixos
  ctx.globalAlpha = 0.6;
  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, H - pad);
  ctx.lineTo(W - pad, H - pad);
  ctx.stroke();
  ctx.globalAlpha = 1;

  // linha
  ctx.beginPath();
  ctx.moveTo(xTo(0), yTo(ys[0]));
  for (let i = 1; i < ys.length; i++) {
    ctx.lineTo(xTo(i), yTo(ys[i]));
  }
  ctx.stroke();

  // labels min/max
  ctx.fillText(`min ${minY.toFixed(4)}`, pad, pad - 10);
  ctx.fillText(`max ${maxY.toFixed(4)}`, pad + 120, pad - 10);
}

function percentChange(current, previous) {
  if (previous == null || previous === 0) return null;
  return ((current - previous) / previous) * 100;
}

(async function main() {
  const history = await loadHistory();

  const repoLink = document.getElementById("repoLink");
  // Se quiser, depois você coloca o link fixo no HTML.
  repoLink.href = "https://github.com/";

  if (!Array.isArray(history) || history.length === 0) {
    document.getElementById("lastBid").textContent = "Sem dados ainda";
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

  // últimos 60 pontos (ajusta se quiser)
  const slice = history.slice(-60).map(x => ({
    bid: Number(x.bid),
    timestamp_iso: x.timestamp_iso,
  }));

  drawLineChart(document.getElementById("chart"), slice);
  document.getElementById("chartMeta").textContent = `Mostrando ${slice.length} pontos (últimos).`;
})();
