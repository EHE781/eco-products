/* ── Geolocation ── */
const BARCELONA = { lat: 41.3851, lon: 2.1734 };
let userPos = { ...BARCELONA };

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

function onGeoSuccess(pos) {
    userPos = { lat: pos.coords.latitude, lon: pos.coords.longitude };
    recomputeKm();
    if (typeof list === "function") list();
}

function initGeolocation() {
    recomputeKm();
    if (!navigator.geolocation) return;
    const overlay = document.getElementById("geoOverlay");
    if (!overlay) return;
    overlay.classList.add("open");

    document.getElementById("geoAllow").addEventListener("click", () => {
        overlay.classList.remove("open");
        navigator.geolocation.getCurrentPosition(onGeoSuccess, () => { }, { timeout: 8000 });
    });
    document.getElementById("geoSkip").addEventListener("click", () => {
        overlay.classList.remove("open");
    });
}
