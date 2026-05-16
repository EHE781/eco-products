from fastapi import APIRouter, Query
from ..services.openfoodfacts import search_food
from ..services.recommender import Recommender
from ..database import haversine_km

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])
_recommender = Recommender()


@router.get("")
async def get_recommendations(
    session_id: str = Query(...),
    user_lat: float = Query(41.3851),
    user_lon: float = Query(2.1734),
    lang: str = Query("es"),
    n: int = Query(5, ge=1, le=20),
):
    results = await search_food("bio ecologico", lang=lang)
    products = results["products"]
    for p in products:
        p["km"] = haversine_km(p["lat"], p["lon"], user_lat, user_lon)

    return _recommender.rank(session_id=session_id, products=products, n=n)
