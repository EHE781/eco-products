/* ── App state & event handlers ── */
let cat    = "all";
let sortBy = "prox";
let q      = "";

function refresh() { list(); }

async function setCat(c) {
    cat = c;
    q   = "";
    const searchInput = document.getElementById("searchInput");
    if (searchInput) searchInput.value = "";
    document.querySelectorAll(".chip").forEach(ch => {
        ch.classList.toggle("on", ch.dataset.cat === c);
    });
    removeIAFilters()
    await loadProducts(CAT_QUERIES[c] || CAT_QUERIES.all);
}

function setSort(val) {
    sortBy = val;
    list();
}

function goToPage(page) {
    const totalDisplayPages = Math.ceil(P_ALL.length / PAGE_SIZE);
    if (page < 1 || page > totalDisplayPages || isLoading) return;
    currentPage = page;
    list();
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (page === totalDisplayPages && P_ALL.length < totalApiCount) {
        prefetchNext();
    }
}

function cardClick(id) {
    const p = P_ALL.find(x => x.id === id);
    if (!p) return;
    logInteraction(id, "view");
    const context = `🛒 ${pname(p)} (${p.cat}, ${p.origin}, ${p._km ?? 0}km)\nNutriscore: ${p.ns} | Ecoscore: ${p.es}\n${pdesc(p)}\nBeneficios: ${pbens(p).join(", ")}`;
    openChat(context);
}

function openModal()  { document.getElementById("geoOverlay").classList.add("open"); }
function closeModal() { document.getElementById("geoOverlay").classList.remove("open"); }

document.addEventListener("DOMContentLoaded", async () => {
    applyLang();
    initChat();
    await loadProducts();
    initGeolocation();

    // Search — debounced API call
    let _searchTimer;
    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
        searchInput.addEventListener("input", e => {
            q = e.target.value.trim();
            list(); // feedback inmediato con productos ya cargados
            clearTimeout(_searchTimer);
            _searchTimer = setTimeout(async () => {
                const query = q ? [q] : (CAT_QUERIES[cat] || CAT_QUERIES.all);
                await loadProducts(query);
            }, 400);
        });
    }
    const searchBtn = document.getElementById("searchBtn");
    if (searchBtn) {
        searchBtn.addEventListener("click", async () => {
            q = searchInput ? searchInput.value.trim() : "";
            clearTimeout(_searchTimer);
            await loadProducts(q ? [q] : (CAT_QUERIES[cat] || CAT_QUERIES.all));
        });
    }

    // Chat
    const chatInput = document.getElementById("chatInput");
    if (chatInput) chatInput.addEventListener("keydown", e => { if (e.key === "Enter") send(); });
    const sendBtn = document.getElementById("sendBtn");
    if (sendBtn) sendBtn.addEventListener("click", send);

    // FAB & chat controls
    const fab = document.getElementById("fab");
    if (fab) fab.addEventListener("click", toggleChat);
    const chatClose = document.getElementById("chatClose");
    if (chatClose) chatClose.addEventListener("click", closeChat);
    const chatNewBtn = document.getElementById("chatNewBtn");
    if (chatNewBtn) chatNewBtn.addEventListener("click", newChat);
    const chatHistBtn = document.getElementById("chatHistBtn");
    if (chatHistBtn) chatHistBtn.addEventListener("click", toggleHistory);

    // Sort
    const sortSel = document.getElementById("sortSel");
    if (sortSel) sortSel.addEventListener("change", e => setSort(e.target.value));

    // Lang
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", () => changeLang(btn.dataset.lang));
    });
});
