import json
from fastapi import APIRouter
from .. import schemas

from app.models import ProducDuckDB
from ..database_duckdb import read_products, clean_filter_forlater
from ..services.llm import generate_filter_using_chat, explain_filter_using_chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(payload: schemas.ChatIn):
    reply = await generate_filter_using_chat(payload.message, payload.context)
    filters = _parse_filter_response_(reply)
    if filters is None:
        return schemas.ChatOut()

    if isinstance(payload.page_query , str) and len(payload.page_query.strip()) >0:
        filters["category"] = payload.page_query
        if "relevant_properties" in filters:
            filters["relevant_properties"] = ",".join([filters["relevant_properties"], "category"])

    filtered = None
    try:
        filtered = read_products(filters, None, 20)
    except Exception:
        pass

    filters = clean_filter_forlater(filters)
    filters_short = _format_filter_for_chat2_(filters)
    print(filters_short)
    reply = await explain_filter_using_chat(payload.message, filters_short, payload.lang)

    return schemas.ChatOut(reply=reply, filtered=filtered, filters=filters)

def _parse_filter_response_(filters:str):
    parsed : ProducDuckDB = None
    try:
        parsed= json.loads(filters)
    except json.JSONDecodeError:
        return None
    return parsed

def _format_filter_for_chat2_(filtes:dict):
    return "\n".join([f"{key}: {filtes[key]["value"]}" for key in filtes.keys()])
