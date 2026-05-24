# routers/off.py
from fastapi import APIRouter, HTTPException, Path, Query

from app.database_duckdb import read_products
from ..services.openfoodfacts import get_product

router = APIRouter(prefix="/api/off", tags=["openfoodfacts"])


@router.get("/search")
async def search_off(
    q: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    lang: str = Query("es", pattern="^(es|en|ca)$"),
):
    return read_products({"category": q}, page, page_size)


@router.get("/product/{barcode}")
async def get_off_product(
    barcode: str = Path(...),
    lang: str = Query("es", pattern="^(es|en|ca)$"),
):
    product = await get_product(barcode, lang=lang)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado en Open Food Facts")
    return product
