# routers/off.py
from fastapi import APIRouter, HTTPException, Path, Query
from ..services.openfoodfacts import get_product, search_food

router = APIRouter(prefix="/api/off", tags=["openfoodfacts"])


@router.get("/search")
async def search_off(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    lang: str = Query("es", pattern="^(es|en|ca)$"),
):
    return await search_food(q, page=page, page_size=page_size, lang=lang)


@router.get("/product/{barcode}")
async def get_off_product(
    barcode: str = Path(...),
    lang: str = Query("es", pattern="^(es|en|ca)$"),
):
    product = await get_product(barcode, lang=lang)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado en Open Food Facts")
    return product
