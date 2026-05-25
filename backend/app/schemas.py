from typing import Optional
from pydantic import BaseModel

from app.models import ProducDuckDB

class ProductOut(BaseModel):
    id: int
    name: str
    desc: str
    cat: str
    origin: str
    lat: float
    lon: float
    km: float
    unit: str
    ns: Optional[str]
    es: Optional[str]
    emoji: Optional[str]
    season: Optional[str]
    year_round: bool
    co2: Optional[float]
    certs: list[str]
    bens: list[str]
    off_barcode: Optional[str] = None

    model_config = {"from_attributes": True}


class InteractionIn(BaseModel):
    session_id: str
    product_id: Optional[int] = None
    action: str
    query: Optional[str] = None
    lang: str = "es"
    user_lat: float = 41.3851
    user_lon: float = 2.1734


class ChatIn(BaseModel):
    message: str
    lang: str = "es"
    page_query: Optional[str] = None
    context: Optional[str] = None
    user_lat: float = 41.3851
    user_lon: float = 2.1734


class ChatOut(BaseModel):
    reply: str = ""
    filtered: Optional[list] = None
    filters: Optional[dict] = None
