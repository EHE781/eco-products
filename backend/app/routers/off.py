# routers/off.py
from fastapi import APIRouter, HTTPException, Path, Query

from app.database_duckdb import read_products
from ..services.openfoodfacts import get_product

router = APIRouter(prefix="/api/off", tags=["openfoodfacts"])


@router.get("/search")
async def search_off(
    q: str = Query(""),
    display_cat: str = Query(""),
    user_lat: float | None = Query(None),
    user_lon: float | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    lang: str = Query("es", pattern="^(es|en|ca)$"),
):
    rq: dict = {}
    if q:
        rq["q"] = q
    if display_cat and display_cat != "all":
        rq["display_cat"] = display_cat
    if user_lat is not None and user_lon is not None:
        rq["user_lat"] = user_lat
        rq["user_lon"] = user_lon
    return read_products(rq, page, page_size)


@router.get("/product/{barcode}")
async def get_off_product(
    barcode: str = Path(...),
    lang: str = Query("es", pattern="^(es|en|ca)$"),
):
    product = await get_product(barcode, lang=lang)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado en Open Food Facts")
    return product
