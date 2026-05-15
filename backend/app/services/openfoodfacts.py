"""
Open Food Facts API client.

Docs:    https://openfoodfacts.github.io/openfoodfacts-python/
API v2:  https://world.openfoodfacts.org/api/v2/product/{barcode}
Search:  https://world.openfoodfacts.org/cgi/search.pl
"""
from typing import Optional

import httpx

BASE_URL = "https://world.openfoodfacts.org"

_FIELDS = (
    "code,product_name,nutriscore_grade,ecoscore_grade,"
    "categories_tags,origins_tags,image_url,nutriments"
)


async def search_food(
    query: str, page: int = 1, page_size: int = 20
) -> list[dict]:
    """Return a list of OFF product dicts matching *query*."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page": page,
        "page_size": page_size,
        "fields": _FIELDS,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BASE_URL}/cgi/search.pl", params=params)
        resp.raise_for_status()
        return resp.json().get("products", [])


async def get_product(barcode: str) -> Optional[dict]:
    """Fetch a single product by EAN barcode. Returns None if not found."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{BASE_URL}/api/v2/product/{barcode}",
            params={"fields": _FIELDS},
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 1:
                return data["product"]
    return None


def extract_scores(off_product: dict) -> dict:
    """Pull nutriscore + ecoscore out of a raw OFF product dict."""
    return {
        "ns": (off_product.get("nutriscore_grade") or "").upper() or None,
        "es_score": (off_product.get("ecoscore_grade") or "").upper() or None,
    }
