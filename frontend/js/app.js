/* ── App state & event handlers ── */
let cat = "all";
let sortBy = "prox";
let q = "";

function refresh() {
    list();
}

function setCat(c) {
    cat = c;
    document.querySelectorAll(".chip").forEach(ch => {
        ch.classList.toggle("on", ch.dataset.cat === c);
    });
    list();
}

function setSort(val) {
    sortBy = val;
    list();
}

function cardClick(id) {
    const p = P.find(x => x.id === id);
    if (!p) return;
    logInteraction(id, "view");
    const context = `🛒 ${pname(p)} (${p.cat}, ${p.origin}, ${p._km ?? 0}km)\nNutriscore: ${p.ns} | Ecoscore: ${p.es} | Precio: €${p.price}/${p.unit}\n${pdesc(p)}\nBeneficios: ${pbens(p).join(", ")}`;
    openChat(context);
}

function openModal() {
    document.getElementById("geoOverlay").classList.add("open");
}

function closeModal() {
    document.getElementById("geoOverlay").classList.remove("open");
}

document.addEventListener("DOMContentLoaded", async () => {
    applyLang();
    initGeolocation();
    initChat();
    await loadProducts(_lang);
    list();

    // Search
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        searchInput.addEventListener("input", e => {
            q = e.target.value.trim();
            list();
        });
    }
    const searchBtn = document.getElementById("searchBtn");
    if (searchBtn) {
        searchBtn.addEventListener("click", () => {
            q = searchInput ? searchInput.value.trim() : "";
            list();
        });
    }

    // Chat send on Enter
    const chatInput = document.getElementById("chatInput");
    if (chatInput) {
        chatInput.addEventListener("keydown", e => {
            if (e.key === "Enter") send();
        });
    }
    const sendBtn = document.getElementById("sendBtn");
    if (sendBtn) sendBtn.addEventListener("click", send);

    // FAB
    const fab = document.getElementById("fab");
    if (fab) fab.addEventListener("click", toggleChat);

    // Chat close
    const chatClose = document.getElementById("chatClose");
    if (chatClose) chatClose.addEventListener("click", closeChat);

    // Sort
    const sortSel = document.getElementById("sortSel");
    if (sortSel) sortSel.addEventListener("change", e => setSort(e.target.value));

    // Lang buttons
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", () => changeLang(btn.dataset.lang));
    });
});
