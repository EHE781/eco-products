let _pmContext = "";
let _pmExtraProducts = [];

function openProductModal(id) {
    const p = P_ALL.find(x => x.id === id) || _pmExtraProducts.find(x => x.id === id);
    if (!p) return;
    logInteraction(id, "view");

    _pmContext = [
        `${pname(p)}${p.brand ? ` (${p.brand})` : ""} — ${p.cat}`,
        `Origen: ${p.origin || "España"} · ${p._km ?? 0}km`,
        `Nutriscore: ${p.ns} | Ecoscore: ${p.es} | NOVA: ${p.nova||"?"}`,
        p.kcal ? `Kcal: ${p.kcal} | Proteínas: ${p.proteins}g | HC: ${p.carbs}g | Grasas: ${p.fat}g | Azúcares: ${p.sugars}g | Sal: ${p.salt}g` : "",
        p.allergens ? `Alérgenos: ${p.allergens}` : "",
        (p.labels||[]).length ? `Certificaciones: ${p.labels.join(", ")}` : "",
        pdesc(p),
    ].filter(Boolean).join("\n");

    // Image column — emoji always visible as placeholder, image fades in on load
    document.getElementById("pmImgCol").innerHTML =
        `<div class="pm-emoji-large">🛒</div>` +
        (p.image_url
            ? `<img class="pm-img" src="${p.image_url}" alt="${pname(p)}" decoding="async"
                   onload="this.classList.add('loaded')" onerror="this.remove()">`
            : "");

    // Info column
    const rat  = rating(p.ns, p.es, p._km ?? 0);
    const bens = pbens(p);
    const certs  = pcerts(p);
    const labels = p.labels || [];

    const novaColors = { "1":"#22c55e","2":"#84cc16","3":"#f97316","4":"#ef4444" };
    const novaLabels = { "1":"Sin procesar","2":"Ing. culinarios","3":"Procesado","4":"Ultraprocesado" };
    const novaBadge = p.nova
        ? `<span class="pm-nova" style="background:${novaColors[p.nova]||"#9ca3af"}">
               NOVA ${p.nova} · ${novaLabels[p.nova]||""}
           </span>`
        : "";

    const hasNut = p.kcal || p.proteins || p.carbs || p.fat;
    const nutTable = hasNut ? `
        <div class="pm-section-title">📊 Información nutricional <small>(por 100g)</small></div>
        <table class="pm-nut-table">
            ${p.kcal    ? `<tr><td>Calorías</td><td><strong>${p.kcal} kcal</strong></td></tr>` : ""}
            ${p.proteins? `<tr><td>Proteínas</td><td>${p.proteins} g</td></tr>` : ""}
            ${p.carbs   ? `<tr><td>Hidratos de carbono</td><td>${p.carbs} g</td></tr>` : ""}
            ${p.sugars  ? `<tr class="pm-nut-sub"><td>— del cual azúcares</td><td>${p.sugars} g</td></tr>` : ""}
            ${p.fat     ? `<tr><td>Grasas</td><td>${p.fat} g</td></tr>` : ""}
            ${p.fat_sat ? `<tr class="pm-nut-sub"><td>— grasas saturadas</td><td>${p.fat_sat} g</td></tr>` : ""}
            ${p.fiber   ? `<tr><td>Fibra</td><td>${p.fiber} g</td></tr>` : ""}
            ${p.salt    ? `<tr><td>Sal</td><td>${p.salt} g</td></tr>` : ""}
        </table>` : "";

    const allergenBadge = p.allergens
        ? `<div class="pm-section-title">⚠️ Alérgenos</div>
           <p class="pm-allergens">${p.allergens}</p>`
        : "";

    const labelBadges = labels.length
        ? `<div class="pm-section-title">🏷️ Certificaciones</div>
           <div class="pm-tags">${labels.map(l => `<span class="cert">${l}</span>`).join("")}</div>`
        : "";

    const extraTags = [...bens, ...certs];

    document.getElementById("pmInfoCol").innerHTML = `
        ${p.brand ? `<div class="pm-brand">${p.brand}</div>` : ""}
        <h2 class="pm-title">${pname(p)}</h2>
        <div class="pm-cat-origin">
            ${translate(CAT_KEYS[p.cat] || "cat_food")}
            ${p.unit ? `· ${p.unit}` : ""}
            · 📍 ${p.origin || "España"}
        </div>
        <div class="pm-top-badges">
            <div class="pm-rating-bar" style="background:${rat.bg};color:${rat.color}">${rat.text}</div>
            ${novaBadge}
        </div>
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
        <div class="pm-dist">
            📍 ${p.origin || "España"}
            · ${translate("score_dist")}: <strong>${distLabel(p._km ?? 0)}</strong>
            · ${(p._km ?? 0).toLocaleString()} km
        </div>
        ${nutTable}
        ${allergenBadge}
        ${labelBadges}
        ${extraTags.length ? `<div class="pm-tags">${extraTags.map(t=>`<span class="cert">${t}</span>`).join("")}</div>` : ""}
        ${pdesc(p) ? `<div class="pm-section-title">🧾 Ingredientes</div><p class="pm-desc">${pdesc(p)}</p>` : ""}
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
