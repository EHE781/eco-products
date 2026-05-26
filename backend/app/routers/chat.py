import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .. import schemas
from ..services.llm import generate_chat_reply_stream

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(payload: schemas.ChatIn):
    async def event_stream():
        try:
            async for event in generate_chat_reply_stream(
                message=payload.message,
                lang=payload.lang,
                context=payload.context or "",
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            logger.error("Chat stream error: %s", exc)
            yield f"data: {json.dumps({'type': 'done', 'reply': '', 'filtered': None})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
