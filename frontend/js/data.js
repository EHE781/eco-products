/* ── Product catalogue — cargado desde Open Food Facts API ── */

let P = []; // empieza vacío, se llena desde la API

// Category → i18n key
const CAT_KEYS = {
    "Alimentación": "cat_food",
    "Lácteos": "cat_dairy",
    "Panadería": "cat_bakery",
    "Bebidas": "cat_drinks",
};

// Sort orders
const SO = {
    prox: () => (a, b) => (a._km ?? 0) - (b._km ?? 0),
    ns:    () => (a, b) => "ABCDE".indexOf(a.ns) - "ABCDE".indexOf(b.ns),
    es:    () => (a, b) => "ABCDE".indexOf(a.es) - "ABCDE".indexOf(b.es),
    price: () => (a, b) => a.price - b.price,
};

function pname(p)  { return p[`name_${_lang}`]  || p.name_es  || p.name  || ""; }
function pdesc(p)  { return p[`desc_${_lang}`]  || p.desc_es  || p.desc  || ""; }
function pbens(p)  { return p[`bens_${_lang}`]  || p.bens_es  || p.bens  || []; }
function pcerts(p) { return p[`certs_${_lang}`] || p.certs_es || p.certs || []; }

async function loadProducts(lang = _lang, userLat = 41.3851, userLon = 2.1734) {
    try {
        const url = `/api/off/search?q=ecologico&lang=${lang}&page_size=50`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        P = (data.products || []).map(p => ({
            // Campos originales de la API
            ...p,
            // Aliases localizados que espera render.js
            name_es: p.name, name_en: p.name, name_ca: p.name,
            desc_es: p.desc, desc_en: p.desc, desc_ca: p.desc,
            bens_es: p.bens, bens_en: p.bens, bens_ca: p.bens,
            certs_es: p.certs, certs_en: p.certs, certs_ca: p.certs,
            // Campos que usa render.js directamente
            _km:   p.km ?? 0,
            yr:    p.year_round ?? true,
            emoji: p.emoji || "🛒",
            price: p.price ?? 0,
        }));

        console.log(`✅ ${P.length} productos cargados desde OFF`);
    } catch (err) {
        console.error("❌ Error cargando productos desde OFF:", err);
        P = [];
    }
}