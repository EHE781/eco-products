"""
services/openfoodfacts.py — adapta la respuesta de OFF al formato interno
"""
from typing import Optional
import httpx

OFF_BASE = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "EcoScan/1.0 (ecoscan@example.com)"}

_FIELDS = (
    "code,product_name,product_name_es,product_name_en,product_name_ca,"
    "nutriscore_grade,ecoscore_grade,ecoscore_data,"
    "categories_tags,origins,labels_tags,"
    "ingredients_text,ingredients_text_es,ingredients_text_en,"
    "nutriments,quantity,image_front_small_url,manufacturing_places"
)


def _map_cat(tags: list[str]) -> str:
    tag_str = " ".join(tags)
    if any(x in tag_str for x in ["dairy", "yogurt", "cheese", "milk"]):
        return "Lácteos"
    if any(x in tag_str for x in ["bread", "bakery", "pastry", "cereal"]):
        return "Panadería"
    if any(x in tag_str for x in ["beverage", "drink", "juice", "water", "tea"]):
        return "Bebidas"
    return "Alimentación"


def _map_product(raw: dict, lang: str = "es") -> dict:
    name = (
        raw.get(f"product_name_{lang}")
        or raw.get("product_name")
        or "Sin nombre"
    )
    desc = (
        raw.get(f"ingredients_text_{lang}")
        or raw.get("ingredients_text")
        or ""
    )[:200]

    ns = (raw.get("nutriscore_grade") or "?").upper()
    es = (raw.get("ecoscore_grade") or "?").upper()
    co2 = raw.get("ecoscore_data", {}).get("agribalyse", {}).get("co2_total") or 0.0
    origin = (
        raw.get("origins")
        or raw.get("manufacturing_places")
        or "Desconocido"
    )
    certs = [
        t.replace("en:", "").replace("-", " ").title()
        for t in raw.get("labels_tags", [])[:4]
    ]
    nutriments = raw.get("nutriments", {})
    bens = []
    if lang == "es":
        if nutriments.get("fiber_100g", 0) > 3:    bens.append("Alto en fibra")
        if nutriments.get("proteins_100g", 0) > 5:  bens.append("Alto en proteína")
        if nutriments.get("sugars_100g", 0) < 5:    bens.append("Bajo en azúcar")
    elif lang == "en":
        if nutriments.get("fiber_100g", 0) > 3:    bens.append("High in fibre")
        if nutriments.get("proteins_100g", 0) > 5:  bens.append("High in protein")
        if nutriments.get("sugars_100g", 0) < 5:    bens.append("Low in sugar")
    else:  # ca
        if nutriments.get("fiber_100g", 0) > 3:    bens.append("Alt en fibra")
        if nutriments.get("proteins_100g", 0) > 5:  bens.append("Alt en proteïna")
        if nutriments.get("sugars_100g", 0) < 5:    bens.append("Baix en sucre")

    barcode = raw.get("code") or ""
    return {
        "id": barcode,
        "name": name,
        "desc": desc,
        "cat": _map_cat(raw.get("categories_tags", [])),
        "origin": origin,
        "lat": 41.3851,
        "lon": 2.1734,
        "km": 0,
        "price": 0.0,
        "unit": raw.get("quantity") or "ud",
        "ns": ns,
        "es": es,
        "emoji": "🛒",
        "season": "Todo el año",
        "year_round": True,
        "co2": round(float(co2), 2),
        "certs": certs,
        "bens": bens,
        "off_barcode": barcode,
        "image_url": raw.get("image_front_small_url") or "",
    }


async def search_food(
    query: str, page: int = 1, page_size: int = 20, lang: str = "es"
) -> dict:
    params = {
        "q": query,
        "page": page,
        "page_size": page_size,
        "fields": _FIELDS,
        "sort_by": "ecoscore_score",
    }
    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        resp = await client.get(f"{OFF_BASE}/api/v2/search", params=params)
        if resp.status_code == 503:
            return {"products": [], "count": 0, "page": page}
        resp.raise_for_status()
        data = resp.json()

    products = [_map_product(p, lang) for p in data.get("products", [])]
    return {"products": products, "count": data.get("count", len(products)), "page": page}


async def get_product(barcode: str, lang: str = "es") -> Optional[dict]:
    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        resp = await client.get(
            f"{OFF_BASE}/api/v2/product/{barcode}",
            params={"fields": _FIELDS},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("status") != 1:
            return None
        return _map_product(data["product"], lang)


def extract_scores(off_product: dict) -> dict:
    return {
        "ns": (off_product.get("nutriscore_grade") or "").upper() or None,
        "es_score": (off_product.get("ecoscore_grade") or "").upper() or None,
    }