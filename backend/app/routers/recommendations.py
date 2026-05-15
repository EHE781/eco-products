from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from ..routers.products import FOOD_CATS, _build_product_out
from ..services.recommender import Recommender

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

_recommender = Recommender()


@router.get("")
def get_recommendations(
    session_id: str = Query(...),
    user_lat: float = Query(41.3851),
    user_lon: float = Query(2.1734),
    lang: str = Query("es"),
    n: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    products = (
        db.query(models.Product)
        .filter(models.Product.cat.in_(FOOD_CATS))
        .all()
    )
    all_products = [_build_product_out(p, lang, user_lat, user_lon) for p in products]
    return _recommender.rank(session_id=session_id, products=all_products, n=n)
