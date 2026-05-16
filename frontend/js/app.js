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
    await loadProducts(CAT_QUERIES[c] || "bio ecologico", 1);
}

function setSort(val) {
    sortBy = val;
    list();
}

async function goToPage(page) {
    const totalPages = Math.ceil(totalCount / PAGE_SIZE);
    if (page < 1 || page > totalPages || isLoading) return;
    await loadProducts(currentQuery, page);
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function cardClick(id) {
    const p = P.find(x => x.id === id);
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
                const query = q || CAT_QUERIES[cat] || "bio ecologico";
                await loadProducts(query, 1);
            }, 400);
        });
    }
    const searchBtn = document.getElementById("searchBtn");
    if (searchBtn) {
        searchBtn.addEventListener("click", async () => {
            q = searchInput ? searchInput.value.trim() : "";
            clearTimeout(_searchTimer);
            await loadProducts(q || CAT_QUERIES[cat] || "bio ecologico", 1);
        });
    }

    // Chat
    const chatInput = document.getElementById("chatInput");
    if (chatInput) chatInput.addEventListener("keydown", e => { if (e.key === "Enter") send(); });
    const sendBtn = document.getElementById("sendBtn");
    if (sendBtn) sendBtn.addEventListener("click", send);

    // FAB & chat close
    const fab = document.getElementById("fab");
    if (fab) fab.addEventListener("click", toggleChat);
    const chatClose = document.getElementById("chatClose");
    if (chatClose) chatClose.addEventListener("click", closeChat);

    // Sort
    const sortSel = document.getElementById("sortSel");
    if (sortSel) sortSel.addEventListener("change", e => setSort(e.target.value));

    // Lang
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", () => changeLang(btn.dataset.lang));
    });
});
