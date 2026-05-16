import math
import logging

logger = logging.getLogger(__name__)

# Engine opcional — no falla si no hay DB
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, DeclarativeBase
    from .config import settings

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    DB_AVAILABLE = True

    class Base(DeclarativeBase):
        pass

except Exception as exc:
    logger.warning("DB no disponible: %s", exc)
    engine = None
    SessionLocal = None
    DB_AVAILABLE = False

    class Base:  # stub para que los modelos no fallen al importar
        metadata = type("M", (), {"create_all": lambda *a, **k: None})()


def get_db():
    if not DB_AVAILABLE or SessionLocal is None:
        raise RuntimeError("Base de datos no configurada")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    if not DB_AVAILABLE:
        return
    from . import models  # noqa
    Base.metadata.create_all(bind=engine)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
