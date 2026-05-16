from fastapi import APIRouter, Query
from ..database import haversine_km
from ..services.openfoodfacts import search_food

router = APIRouter(prefix="/api/products", tags=["products"])

FOOD_CATS = {"Alimentación", "Lácteos", "Panadería", "Bebidas"}

# Términos de búsqueda por defecto para simular un catálogo local
DEFAULT_QUERIES = ["bio ecologico barcelona", "yogur bio", "pan espelta", "zumo fruta"]


async def _get_catalog(q: str, lang: str, user_lat: float, user_lon: float) -> list[dict]:
    results = await search_food(q, page=1, page_size=20, lang=lang)
    products = results["products"]

    for p in products:
        p["km"] = haversine_km(p["lat"], p["lon"], user_lat, user_lon)

    return sorted(products, key=lambda x: x["km"])


@router.get("")
async def list_products(
    lang: str = Query("es", pattern="^(es|en|ca)$"),
    user_lat: float = Query(41.3851),
    user_lon: float = Query(2.1734),
    q: str = Query("bio ecologico"),
):
    return await _get_catalog(q, lang, user_lat, user_lon)
