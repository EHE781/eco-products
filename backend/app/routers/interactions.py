from fastapi import APIRouter
from .. import schemas

router = APIRouter(prefix="/api/interactions", tags=["interactions"])

_log: list[dict] = []  # en memoria, se pierde al reiniciar


@router.post("", status_code=204)
def log_interaction(body: schemas.InteractionIn):
    _log.append(body.model_dump())  # solo en RAM, sin DB