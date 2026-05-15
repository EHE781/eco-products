"""
Open Food Facts proxy endpoints.

Docs: https://openfoodfacts.github.io/openfoodfacts-python/
API:  https://world.openfoodfacts.org/api/v2/
"""
from fastapi import APIRouter, HTTPException, Path, Query

from ..services.openfoodfacts import get_product, search_food

router = APIRouter(prefix="/api/off", tags=["openfoodfacts"])


@router.get("/search")
async def search_off(
    q: str = Query(..., min_length=2, description="Food product search terms"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """Search Open Food Facts for food products."""
    return await search_food(q, page=page, page_size=page_size)


@router.get("/product/{barcode}")
async def get_off_product(barcode: str = Path(..., description="EAN barcode")):
    """Fetch a single product by barcode from Open Food Facts."""
    product = await get_product(barcode)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found on Open Food Facts")
    return product
