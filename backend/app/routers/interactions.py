from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("", status_code=204)
def log_interaction(body: schemas.InteractionIn, db: Session = Depends(get_db)):
    interaction = models.Interaction(
        session_id=body.session_id,
        product_id=body.product_id,
        action=body.action,
        query=body.query,
        lang=body.lang,
        user_lat=body.user_lat,
        user_lon=body.user_lon,
    )
    db.add(interaction)
    db.commit()
