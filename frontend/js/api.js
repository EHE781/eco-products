/* ── API / interaction logging ── */
const API_BASE = "";   // same origin when served by FastAPI
const sessionId = crypto.randomUUID();

async function logInteraction(productId, action, query = "") {
    try {
        await fetch(`${API_BASE}/api/interactions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId,
                product_id: productId || null,
                action,
                query,
                lang: _lang,
                user_lat: userPos.lat,
                user_lon: userPos.lon,
            }),
        });
    } catch (_) { /* non-critical */ }
}

async function fetchProducts() {
    try {
        const resp = await fetch(
            `${API_BASE}/api/products?lang=${_lang}&user_lat=${userPos.lat}&user_lon=${userPos.lon}`
        );
        if (!resp.ok) return null;
        return await resp.json();
    } catch (_) {
        return null;
    }
}
