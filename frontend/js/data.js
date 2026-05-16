/* ── Product catalogue — cargado desde Open Food Facts API ── */

let P = [];

const PAGE_SIZE = 20;
const MAX_PAGES = 20;
let currentPage  = 1;
let totalCount   = 0;
let currentQuery = "bio ecologico";
let isLoading    = false;

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

const _pageCache = new Map(); // clave: "query::page::lang"

async function loadProducts(query = currentQuery, page = 1) {
    if (isLoading) return;

    // Hit de caché — sin llamada a la API
    const cacheKey = `${query}::${page}::${_lang}`;
    const cached = _pageCache.get(cacheKey);
    if (cached) {
        P            = cached.products;
        currentQuery = query;
        currentPage  = page;
        totalCount   = cached.count;
        list();
        return;
    }

    const prevP     = P;
    const prevCount = totalCount;
    const prevPage  = currentPage;
    const prevQuery = currentQuery;
    const initial   = P.length === 0;

    isLoading = true;
    if (initial) {
        list(); // skeletons solo en carga inicial
    } else {
        document.getElementById("grid")?.classList.add("grid-loading");
    }

    try {
        const url = `/api/off/search?q=${encodeURIComponent(query)}&lang=${_lang}&page=${page}&page_size=${PAGE_SIZE}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        const products = (data.products || []).map(_mapProduct);
        const count    = Math.min(data.count || 0, MAX_PAGES * PAGE_SIZE);

        _pageCache.set(cacheKey, { products, count });

        P            = products;
        currentQuery = query;
        currentPage  = page;
        totalCount   = count;
    } catch (err) {
        console.error("Error cargando productos:", err);
        P            = prevP;
        totalCount   = prevCount;
        currentPage  = prevPage;
        currentQuery = prevQuery;
    } finally {
        isLoading = false;
        document.getElementById("grid")?.classList.remove("grid-loading");
        list();
    }
}
