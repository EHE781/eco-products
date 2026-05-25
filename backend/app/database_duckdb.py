"""DuckDB product store"""

import re
import sqlalchemy
from sqlalchemy import func, select, text, create_engine
from sqlalchemy.orm import Session

from .config import settings
from .models import ProducDuckDB
from .constants import FOOD_SAFTY_RANGES, NUTRISCORE_GRADE

_engine_ = create_engine(f"duckdb:///{settings.DATABASE_DUCKDB}")
_con_    = Session(_engine_)


def _grade(val: str | None) -> str | None:
    return val.strip().upper() if val and val.strip() else None


def _serialize(p: ProducDuckDB) -> dict:
    return {
        "id":         p.id or "",
        "name":       p.name or "",
        "cat":        p.cat or "",
        "origin":     p.origin or "",
        "ns":         _grade(p.ns),
        "es":         _grade(p.es),
        "co2":        float(p.co2) if p.co2 else 0.0,
        "image_url":  p.image_url or None,
        "desc":       p.desc or "",
        "bens":       [],
        "certs":      [],
        "km":         0,
        "lat":        0.0,
        "lon":        0.0,
        "year_round": True,
        "emoji":      None,
    }


def _base_query(rq: dict):
    """Build the filtered query (no ORDER BY / LIMIT yet)."""
    query = (
        select(ProducDuckDB)
        .filter(ProducDuckDB.ns.in_(NUTRISCORE_GRADE))
        .filter(ProducDuckDB.name.isnot(None))
        .filter(ProducDuckDB.name != "")
        .filter(ProducDuckDB.countries_tags.contains("en:spain"))
    )

    # Free-text search across product name and categories
    if _is_relevant_(rq, "q"):
        raw   = [t.strip() for t in rq["q"].replace(",", " ").split() if t.strip()]
        pos   = [t       for t in raw if not t.startswith("-") and len(t) > 2]
        neg   = [t[1:]   for t in raw if     t.startswith("-") and len(t) > 3]
        if pos:
            conditions = [
                cond
                for t in pos
                for cond in (
                    ProducDuckDB.name.ilike(f"%{t}%"),
                    ProducDuckDB.cat.ilike(f"%{t}%"),
                )
            ]
            query = query.filter(sqlalchemy.or_(*conditions))
        for t in neg:
            query = query.filter(sqlalchemy.not_(ProducDuckDB.cat.ilike(f"%{t}%")))

    # Nutritional filters
    if _is_relevant_(rq, "nutriscore"):
        query = query.filter(ProducDuckDB.ns == rq["nutriscore"])
    if _is_relevant_(rq, "sugars_100g"):
        query = _add_range_filter_(query, rq, "sugars_100g", ProducDuckDB.sugars_100g)
    if _is_relevant_(rq, "fat_100g"):
        query = _add_range_filter_(query, rq, "fat_100g", ProducDuckDB.fat_100g)
    if _is_relevant_(rq, "saturated-fat_100g"):
        query = _add_range_filter_(query, rq, "saturated-fat_100g", ProducDuckDB.fat_sat_100g)
    if _is_relevant_(rq, "fiber_100g"):
        query = _add_range_filter_(query, rq, "fiber_100g", ProducDuckDB.fiber_100g)
    if _is_relevant_(rq, "salt_100g"):
        query = _add_range_filter_(query, rq, "salt_100g", ProducDuckDB.salt_100g)
    if _is_relevant_(rq, "dangerous_allergens"):
        query = _add_contains_filter_(query, rq, "dangerous_allergens", ProducDuckDB.allergens, True, "en:none")

    return query


def read_products(rq: dict, page: int | None, page_size: int):
    page   = page or 1
    offset = (page - 1) * page_size

    base  = _base_query(rq)
    total = _con_.execute(select(func.count()).select_from(base.subquery())).scalar() or 0

    rows = [
        item[0]
        for item in _con_.execute(
            base.order_by(ProducDuckDB.name).offset(offset).limit(page_size)
        ).all()
    ]

    return {"products": [_serialize(r) for r in rows], "count": total, "page": page}


_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC|EXECUTE|PRAGMA|ATTACH|DETACH|COPY|EXPORT|IMPORT)\b",
    re.IGNORECASE,
)

def execute_readonly_query(sql: str, max_rows: int = 50) -> list[dict]:
    """Execute a read-only SQL query. Raises ValueError for anything that isn't a plain SELECT."""
    stripped = sql.strip()
    if not stripped.upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    if _FORBIDDEN.search(stripped):
        raise ValueError("Query contains a forbidden keyword")
    result = _con_.execute(text(stripped))
    cols = list(result.keys())
    return [dict(zip(cols, row)) for row in result.fetchmany(max_rows)]


def clean_filter_forlater(rq: dict):
    """Format filter for AI chat / frontend display."""
    cleaned = {}
    for key in [k for k in rq if _is_relevant_(rq, k)]:
        cleaned[key] = {"value": rq[key], "type": "value"}
        if key.endswith("100g"):
            cleaned[key]["type"]  = "range"
            cleaned[key]["range"] = _get_range_lvl_(rq, key)
    return cleaned


# ── Internal helpers ──────────────────────────────────────────────────────────

def _is_relevant_(rq: dict, key: str):
    return key in rq and rq[key] is not None and (
        "relevant_properties" not in rq or rq["relevant_properties"].find(key) != -1
    )


def _add_range_filter_(query, rq, key, column):
    config = FOOD_SAFTY_RANGES[key]
    values = config[_get_range_lvl_(rq, key)]
    vmin   = values["start"]
    vmax   = values.get("end", 999999)
    return query.filter((column >= vmin) & (column < vmax))


def _add_contains_filter_(query, rq, key, column, negative: bool, negative_flag: str = None):
    for item in [v.strip() for v in rq[key].split(",")]:
        if negative:
            query = query.filter(column.isnot(None)).filter(column != "")
            if negative_flag:
                query = query.filter(
                    sqlalchemy.or_(sqlalchemy.not_(column.contains(item)), column == negative_flag)
                )
            else:
                query = query.filter(sqlalchemy.not_(column.contains(item)))
        else:
            query = query.filter(column.contains(item))
    return query


def _get_range_lvl_(rq: dict, key: str):
    config = FOOD_SAFTY_RANGES[key]
    for level in ["low", "middle", "high"]:
        cfg = config[level]
        if cfg["start"] < rq[key] and ("end" not in cfg or rq[key] < cfg["end"]):
            return level
    return "low"
