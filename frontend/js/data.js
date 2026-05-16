/* ── Product catalogue — cargado desde Open Food Facts API ── */

let P_ALL = [];

const FETCH_SIZE  = 50;
const PAGE_SIZE   = 15;
const MAX_BATCHES = 8; // tope: 400 productos

let apiBatch      = 0;
let totalApiCount = 0;
let currentPage   = 1;
let currentQuery  = "bio ecologico";
let isLoading     = false;
let isPrefetching = false;

const CAT_KEYS = {
    "Alimentación": "cat_food",
    "Lácteos":      "cat_dairy",
    "Panadería":    "cat_bakery",
    "Bebidas":      "cat_drinks",
};

const CAT_QUERIES = {
    "all":          "bio ecologico",
    "Alimentación": "alimentos bio ecologicos",
    "Lácteos":      "lacteos bio ecologicos",
    "Panadería":    "pan espelta bio ecologico",
    "Bebidas":      "bebidas bio ecologicas",
};

const SO = {
    prox: () => (a, b) => (a._km ?? 0) - (b._km ?? 0),
    ns:   () => (a, b) => "ABCDE".indexOf(a.ns) - "ABCDE".indexOf(b.ns),
    es:   () => (a, b) => "ABCDE".indexOf(a.es) - "ABCDE".indexOf(b.es),
};

function pname(p)  { return p[`name_${_lang}`]  || p.name_es  || p.name  || ""; }
function pdesc(p)  { return p[`desc_${_lang}`]  || p.desc_es  || p.desc  || ""; }
function pbens(p)  { return p[`bens_${_lang}`]  || p.bens_es  || p.bens  || []; }
function pcerts(p) { return p[`certs_${_lang}`] || p.certs_es || p.certs || []; }

function _mapProduct(p) {
    return {
        ...p,
        name_es: p.name, name_en: p.name, name_ca: p.name,
        desc_es: p.desc, desc_en: p.desc, desc_ca: p.desc,
        bens_es: p.bens, bens_en: p.bens, bens_ca: p.bens,
        certs_es: p.certs, certs_en: p.certs, certs_ca: p.certs,
        _km:   p.km ?? 0,
        yr:    p.year_round ?? true,
        emoji: p.emoji || "🛒",
    };
}

async function _fetchBatch(query, batch) {
    const url = `/api/off/search?q=${encodeURIComponent(query)}&lang=${_lang}&page=${batch}&page_size=${FETCH_SIZE}`;
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    if (batch === 1) {
        totalApiCount = Math.min(data.count || 0, MAX_BATCHES * FETCH_SIZE);
    }
    return (data.products || []).map(_mapProduct);
}

async function loadProducts(query = currentQuery) {
    if (isLoading) return;

    const prevAll   = P_ALL;
    const prevCount = totalApiCount;
    const prevQuery = currentQuery;

    isLoading    = true;
    currentPage  = 1;
    currentQuery = query;

    if (P_ALL.length === 0) {
        // Carga inicial: mostrar skeletons
        apiBatch      = 0;
        totalApiCount = 0;
        list();
    } else {
        // Nueva búsqueda: mantener resultados actuales visibles mientras carga
        document.getElementById("grid")?.classList.add("grid-loading");
    }

    try {
        const products = await _fetchBatch(query, 1);
        P_ALL    = products;
        apiBatch = 1;
    } catch (err) {
        console.error("Error cargando productos:", err);
        P_ALL         = prevAll;
        totalApiCount = prevCount;
        currentQuery  = prevQuery;
    } finally {
        isLoading = false;
        document.getElementById("grid")?.classList.remove("grid-loading");
        list();
    }
}

async function prefetchNext() {
    if (isPrefetching || isLoading)    return;
    if (P_ALL.length >= totalApiCount) return;
    if (apiBatch >= MAX_BATCHES)       return;

    isPrefetching = true;
    try {
        const products = await _fetchBatch(currentQuery, apiBatch + 1);
        if (products.length > 0) {
            P_ALL = [...P_ALL, ...products];
            apiBatch++;
            list(); // extiende la paginación visualmente
        }
    } catch (err) {
        console.error("Prefetch error:", err);
    } finally {
        isPrefetching = false;
    }
}
