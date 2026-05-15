from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db, haversine_km
from .. import models, schemas

router = APIRouter(prefix="/api/products", tags=["products"])

# Food-only categories (cosmetics and cleaning products excluded)
FOOD_CATS = {"Alimentación", "Lácteos", "Panadería", "Bebidas"}


def _build_product_out(
    p: models.Product, lang: str, user_lat: float, user_lon: float
) -> dict:
    name = getattr(p, f"name_{lang}", None) or p.name_es
    desc = getattr(p, f"desc_{lang}", None) or p.desc_es or ""
    km = haversine_km(p.lat, p.lon, user_lat, user_lon)
    certs = [c.cert for c in p.certs if c.lang == lang]
    bens = [b.benefit for b in p.benefits if b.lang == lang]
    return {
        "id": p.id,
        "name": name,
        "desc": desc,
        "cat": p.cat,
        "origin": p.origin,
        "lat": p.lat,
        "lon": p.lon,
        "km": km,
        "price": p.price,
        "unit": p.unit,
        "ns": p.ns,
        "es": p.es_score,
        "emoji": p.emoji,
        "season": p.season,
        "year_round": p.year_round,
        "co2": p.co2,
        "certs": certs,
        "bens": bens,
        "off_barcode": p.off_barcode,
    }


@router.get("", response_model=list[schemas.ProductOut])
def list_products(
    lang: str = Query("es", pattern="^(es|en|ca)$"),
    user_lat: float = Query(41.3851),
    user_lon: float = Query(2.1734),
    db: Session = Depends(get_db),
):
    products = (
        db.query(models.Product)
        .filter(models.Product.cat.in_(FOOD_CATS))
        .all()
    )
    result = [_build_product_out(p, lang, user_lat, user_lon) for p in products]
    return sorted(result, key=lambda x: x["km"])
