/* ── Rendering helpers ── */
const SCORE_COLORS = { A: "#038141", B: "#85BB2F", C: "#FECB02", D: "#EF7D00", E: "#E63312" };

function scoreColor(s) {
    return SCORE_COLORS[s] || "#9CA3AF";
}

function distColor(km) {
    if (km <= 50) return "#038141";
    if (km <= 200) return "#85BB2F";
    if (km <= 500) return "#FECB02";
    if (km <= 1500) return "#EF7D00";
    return "#E63312";
}

function distPct(km) {
    return Math.min(100, Math.round(Math.log10(Math.max(1, km) + 1) / Math.log10(21001) * 100));
}

function distLabel(km) {
    if (km <= 50) return t("dist_very_close");
    if (km <= 200) return t("dist_close");
    if (km <= 500) return t("dist_regional");
    if (km <= 1500) return t("dist_national");
    return t("dist_intl");
}

function rating(ns, es, km) {
    const scoreIdx = s => "ABCDE".indexOf(s ?? "C");
    const avg = (scoreIdx(ns) + scoreIdx(es)) / 2;
    const distPenalty = km > 1500 ? 2 : km > 500 ? 1 : 0;
    const total = avg + distPenalty;
    if (total < 1) return { text: t("rating_excellent"), bg: "#D1FAE5", color: "#065F46" };
    if (total < 2) return { text: t("rating_good"), bg: "#DCFCE7", color: "#14532D" };
    if (total < 3.5) return { text: t("rating_ok"), bg: "#FEF9C3", color: "#713F12" };
    return { text: t("rating_consider"), bg: "#FEE2E2", color: "#7F1D1D" };
}

function nsScale(score, type) {
    const letters = ["A", "B", "C", "D", "E"];
    return letters.map(l => {
        const cls = `ns-l nl-${l.toLowerCase()}${l === score ? " active" : ""}${score == null ? " na" : ""}`;
        return `<span class="${cls}">${l}</span>`;
    }).join("");
}

function render(p) {
    const km = p._km ?? 0;
    const rat = rating(p.ns, p.es, km);
    const co2Pos = p.co2 > 0;
    const certsHtml = pcerts(p).map(c => `<span class="cert">${c}</span>`).join("");

    return `
<article class="card" data-id="${p.id}" onclick="cardClick(${p.id})">
  <div class="card-top">
    <div class="p-emoji">${p.emoji}</div>
    <div class="p-meta">
      <div class="p-cat">${t(CAT_KEYS[p.cat] || "cat_food")}</div>
      <div class="p-name">${pname(p)}</div>
      <div class="p-origin">📍 ${p.origin}</div>
    </div>
    ${!p.yr ? `<span class="season">${p.season}</span>` : ""}
  </div>
  <div class="rating-bar" style="background:${rat.bg};color:${rat.color}">${rat.text}</div>
  <div class="scores-row">
    <div class="score-col">
      <div class="score-label">${t("score_ns")}</div>
      <div class="ns-scale">${nsScale(p.ns, "ns")}</div>
    </div>
    <div class="score-col">
      <div class="score-label">${t("score_es")}</div>
      <div class="ns-scale">${nsScale(p.es, "es")}</div>
    </div>
    <div class="price-col">
      <div class="price-val">€${p.price.toFixed(2)}</div>
      <div class="price-unit">/${p.unit}</div>
      <div class="co2-tag" style="color:${co2Pos ? "#16a34a" : "#dc2626"}">
        ${co2Pos ? "+" : ""}${p.co2} ${t(co2Pos ? "co2_saved" : "co2_added")}
      </div>
    </div>
  </div>
  <div class="dist-section">
    <div class="dist-header">
      <span>${t("score_dist")}: <strong>${distLabel(km)}</strong></span>
      <span>${km.toLocaleString()} km</span>
    </div>
    <div class="dist-bar"><div class="dist-fill" style="width:${distPct(km)}%;background:${distColor(km)}"></div></div>
  </div>
  ${certsHtml ? `<div class="card-foot">${certsHtml}</div>` : ""}
</article>`;
}

function list() {
    const container = document.getElementById("grid");
    const countEl = document.getElementById("count");
    if (!container) return;

    let items = P.filter(p => {
        if (cat !== "all" && p.cat !== cat) return false;
        if (!q) return true;
        const needle = q.toLowerCase();
        return [pname(p), p.cat, p.origin, pdesc(p)].some(s => s.toLowerCase().includes(needle));
    });

    const sorter = SO[sortBy] ? SO[sortBy]() : SO.prox();
    items.sort(sorter);

    if (countEl) countEl.textContent = `${t("showing")} ${items.length} ${t("showing2")}`;

    if (items.length === 0) {
        container.innerHTML = `<div class="no-r"><div class="no-r-i">🌿</div><strong>${t("no_results")}</strong><p>${t("no_results_sub")}</p></div>`;
        return;
    }

    container.innerHTML = items.map(render).join("");
    updateHeroStats(items);
}

function updateHeroStats(items) {
    const total = items.length;
    const local = items.filter(p => (p._km ?? 0) <= 200).length;
    const pctLocal = total ? Math.round(local / total * 100) : 0;
    const nsA = items.filter(p => p.ns === "A").length;
    const co2 = items.reduce((s, p) => s + (p.co2 > 0 ? p.co2 : 0), 0);

    const elN = document.getElementById("statN");
    const elLocal = document.getElementById("statLocal");
    const elNS = document.getElementById("statNS");
    const elCO2 = document.getElementById("statCO2");

    if (elN) elN.textContent = total;
    if (elLocal) elLocal.textContent = pctLocal + "%";
    if (elNS) elNS.textContent = nsA;
    if (elCO2) elCO2.textContent = co2.toFixed(1);
}
