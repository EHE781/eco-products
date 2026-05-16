from fastapi import APIRouter
from ..services.openfoodfacts import search_food
from ..services.llm import build_system_prompt, generate_chat_reply
from .. import schemas
from ..database import haversine_km

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatOut)
async def chat(payload: schemas.ChatIn):
    results = await search_food("bio ecologico", lang=payload.lang)
    catalog = results["products"]
    for p in catalog:
        p["km"] = haversine_km(p["lat"], p["lon"], payload.user_lat, payload.user_lon)

    system_prompt = build_system_prompt(catalog, payload.lang, payload.context)
    reply = generate_chat_reply(payload.message, system_prompt)
    return schemas.ChatOut(reply=reply)