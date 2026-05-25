let _pmContext = "";
let _pmExtraProducts = [];

function openProductModal(id) {
    const p = P_ALL.find(x => x.id === id) || _pmExtraProducts.find(x => x.id === id);
    if (!p) return;
    logInteraction(id, "view");

    _pmContext = [
        `${pname(p)} (${p.cat})`,
        `Origen: ${p.origin} · ${p._km ?? 0}km`,
        `Nutriscore: ${p.ns} | Ecoscore: ${p.es} | CO2: ${p.co2}kg/100g`,
        pdesc(p),
    ].filter(Boolean).join("\n");

    // Image column
    document.getElementById("pmImgCol").innerHTML = p.image_url
        ? `<img class="pm-img" src="${p.image_url}" alt="${pname(p)}"
               onerror="this.outerHTML='<div class=\\'pm-emoji-large\\'>${p.emoji}</div>'">`
        : `<div class="pm-emoji-large">${p.emoji}</div>`;

    // Info column
    const rat = rating(p.ns, p.es, p._km ?? 0);
    const co2Pos = p.co2 > 0;
    const bens = pbens(p);
    const certs = pcerts(p);
    document.getElementById("pmInfoCol").innerHTML = `
        <h2 class="pm-title">${pname(p)}</h2>
        <div class="pm-cat-origin">${translate(CAT_KEYS[p.cat] || "cat_food")} · 📍 ${p.origin}</div>
        <div class="pm-rating-bar" style="background:${rat.bg};color:${rat.color}">${rat.text}</div>
        <div class="pm-scores">
            <div class="pm-score-row">
                <span class="pm-score-lbl">${translate("score_ns")}</span>
                <div class="ns-scale">${nsScale(p.ns, "ns")}</div>
            </div>
            <div class="pm-score-row">
                <span class="pm-score-lbl">${translate("score_es")}</span>
                <div class="ns-scale">${nsScale(p.es, "es")}</div>
            </div>
        </div>
        <div class="pm-co2" style="color:${co2Pos ? "#16a34a" : "#dc2626"}">
            ${co2Pos ? "+" : ""}${p.co2} ${translate(co2Pos ? "co2_saved" : "co2_added")}
        </div>
        <div class="pm-dist">
            ${translate("score_dist")}: <strong>${distLabel(p._km ?? 0)}</strong>
            · ${(p._km ?? 0).toLocaleString()} km
        </div>
        ${pdesc(p) ? `<p class="pm-desc">${pdesc(p)}</p>` : ""}
        ${bens.length || certs.length ? `
            <div class="pm-tags">
                ${[...bens, ...certs].map(t => `<span class="cert">${t}</span>`).join("")}
            </div>` : ""}
    `;

    // Init modal chat
    const msgs = document.getElementById("pmChatMsgs");
    msgs.innerHTML = "";
    _addPmMsg("bot", `¡Hola! Puedo contarte todo sobre **${pname(p)}** 🌿 ¿Tienes alguna pregunta sobre sus ingredientes, valor nutricional o impacto ambiental?`);

    document.getElementById("pmChatInput").placeholder = translate("chat_ph");
    document.getElementById("productModal").classList.add("open");
    document.getElementById("pmChatInput").focus();
}

function closeProductModal() {
    document.getElementById("productModal").classList.remove("open");
    _pmContext = "";
}

function _addPmMsg(role, text) {
    const msgs = document.getElementById("pmChatMsgs");
    if (!msgs) return;
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    if (role === "bot") div.innerHTML = _md(text);
    else div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
}

async function sendPm() {
    const inp = document.getElementById("pmChatInput");
    if (!inp) return;
    const msg = inp.value.trim();
    if (!msg) return;
    inp.value = "";

    _addPmMsg("user", msg);
    logInteraction(null, "chat", msg);

    const msgs = document.getElementById("pmChatMsgs");
    try {
        const result = await callBackendChat(msg, msgs, _pmContext);
        if (result?.filtered?.products?.length > 0) {
            _pmExtraProducts = result.filtered.products.map(_mapProduct);
        }
    } catch {
        _addPmMsg("bot", fallback(msg));
    }
}
