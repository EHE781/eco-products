/* ── Geolocation ── */
const BARCELONA = { lat: 41.3851, lon: 2.1734 };
let userPos = { ...BARCELONA };
let hasRealLocation = false;

function haversine(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function recomputeKm() {
    P_ALL.forEach(p => { p._km = Math.round(haversine(userPos.lat, userPos.lon, p.lat, p.lon)); });
}

function _setLocBadge(text, loading = false) {
    const el = document.getElementById("locBadge");
    if (!el) return;
    el.textContent = loading ? `⏳ ${text}` : `📍 ${text}`;
}

async function _reverseGeocode(lat, lon) {
    try {
        const resp = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
            { headers: { "Accept-Language": "es" } }
        );
        if (!resp.ok) return null;
        const data = await resp.json();
        return data.address?.city || data.address?.town || data.address?.village || data.address?.county || null;
    } catch {
        return null;
    }
}

async function _forwardGeocode(city) {
    try {
        const resp = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(city)}&format=json&limit=1`,
            { headers: { "Accept-Language": "es" } }
        );
        if (!resp.ok) return null;
        const data = await resp.json();
        if (!data.length) return null;
        return { lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon), name: data[0].display_name.split(",")[0] };
    } catch {
        return null;
    }
}

async function _applyLocation(lat, lon, label) {
    userPos = { lat, lon };
    hasRealLocation = true;
    recomputeKm();
    _setLocBadge(label);

    const sortSel = document.getElementById("sortSel");
    if (sortSel) { sortSel.value = "prox"; sortBy = "prox"; }

    if (typeof loadProducts === "function") await loadProducts(currentQuery);
    else if (typeof list === "function") list();
}

/* ── Modal controls ── */
function requestGeolocation() {
    const overlay = document.getElementById("locOverlay");
    if (overlay) {
        const inp = document.getElementById("locCityInput");
        const err = document.getElementById("locCityError");
        if (inp) inp.value = "";
        if (err) err.textContent = "";
        overlay.classList.add("open");
        setTimeout(() => { if (inp) inp.focus(); }, 50);
    }
}

function closeLocModal() {
    document.getElementById("locOverlay")?.classList.remove("open");
}

function locUseGeo() {
    if (!navigator.geolocation) return;
    closeLocModal();
    _setLocBadge("Localizando…", true);
    navigator.geolocation.getCurrentPosition(
        async (pos) => {
            const city = await _reverseGeocode(pos.coords.latitude, pos.coords.longitude);
            await _applyLocation(pos.coords.latitude, pos.coords.longitude, city || "Tu ubicación");
        },
        () => { _setLocBadge("España"); },
        { timeout: 10000 }
    );
}

async function locUseCity() {
    const inp = document.getElementById("locCityInput");
    const err = document.getElementById("locCityError");
    const city = inp?.value.trim();
    if (!city) return;

    if (err) err.textContent = "";
    if (inp) inp.disabled = true;

    const result = await _forwardGeocode(city);

    if (inp) inp.disabled = false;

    if (!result) {
        if (err) err.textContent = "Ciudad no encontrada. Prueba con otro nombre.";
        return;
    }

    closeLocModal();
    await _applyLocation(result.lat, result.lon, result.name);
}

function initGeolocation() {
    recomputeKm();

    // Enter on city input submits
    document.getElementById("locCityInput")?.addEventListener("keydown", e => {
        if (e.key === "Enter") locUseCity();
    });

    // Close on backdrop click
    document.getElementById("locOverlay")?.addEventListener("click", e => {
        if (e.target === document.getElementById("locOverlay")) closeLocModal();
    });

    if (!navigator.geolocation) return;

    // If already granted, apply silently without showing modal
    navigator.permissions?.query({ name: "geolocation" }).then(result => {
        if (result.state === "granted") {
            _setLocBadge("Localizando…", true);
            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    const city = await _reverseGeocode(pos.coords.latitude, pos.coords.longitude);
                    await _applyLocation(pos.coords.latitude, pos.coords.longitude, city || "Tu ubicación");
                },
                () => { _setLocBadge("España"); },
                { timeout: 10000 }
            );
        }
    }).catch(() => { /* permissions API not available */ });
}
