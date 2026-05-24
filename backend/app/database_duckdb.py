"""Database"""

import sqlalchemy
from .config import settings

from app.models import ProducDuckDB
from sqlalchemy.orm import Session
from sqlalchemy import Select, Tuple, create_engine, select
from app.constants import FOOD_SAFTY_RANGES, NUTRISCORE_GRADE

_con_ = None
_engine_ = None
if _con_ is None:
    _engine_ = create_engine(f"duckdb:///{settings.DATABASE_DUCKDB}")
    _con_ = Session(_engine_)

def read_products(rq:dict, page:int | None, page_size: int):
    """Query products"""
    query = select(ProducDuckDB)\
        .filter(ProducDuckDB.ns.in_(NUTRISCORE_GRADE))\
        .where((ProducDuckDB.name != '') & (ProducDuckDB.name is not None))
        
    if _is_relevant_(rq, "nutriscore"):
        query = query.where(ProducDuckDB.ns == rq['nutriscore'])
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
    if _is_relevant_(rq, "category"):
        if rq["category"].find("-food"): #por alguna razón mágica hay una cateogria: food and beverage, que rompe la busqueda de bebidas y lacteos, esto lo arregla
            query = query.filter(sqlalchemy.not_(ProducDuckDB.cat.contains("food")))
        query = _add_or_contains_filter_(query, rq, "category", ProducDuckDB.cat)
    query = query.order_by(ProducDuckDB.name)
    query = query.limit(page_size)

    print(query.compile(_engine_)) # para confirmar si la query es correcta

    rows : list[ProducDuckDB] = [item[0] for item in _con_.execute(query).all()]
    return {"products": rows, "count": len(rows), "page": page}

def clean_filter_forlater(rq:dict):
    """ Format filter for ai chat use, and for frontend """

    cleaned = {}
    for key in  [key for key in rq.keys() if _is_relevant_(rq, key)]:
        cleaned[key] = {"value": rq[key], "type": "value"}
        if key.endswith("100g"):
            cleaned[key]["type"] = "range"
            cleaned[key]["range"] = _get_range_lvl_(rq, key)
    return cleaned

def _is_relevant_(rq: dict, key: str):
    return key in rq and rq[key] is not None and \
        ("relevant_properties" not in rq or rq["relevant_properties"].find(key) != -1)

def _add_range_filter_(query :Select[Tuple], rq: dict, key:str, column: Tuple):
    config = FOOD_SAFTY_RANGES[key]
    values =  config[_get_range_lvl_(rq, key)]
    [vmin, vmax] = [values["start"], values["end"] if "end" in values else 999999]
    return query.where((column >= vmin) & (column < vmax))

def _add_contains_filter_(query :Select[Tuple], rq: dict, key:str, column: Tuple, negative: bool, negative_flag: str = None):
    for item in [val.strip() for val in rq[key].split(",")]:
        if negative:
            query = query.filter((column != '') & (column is not None))
            if isinstance(negative_flag, str) and len(negative_flag.strip())>0:
                query = query.filter(sqlalchemy.or_(*[sqlalchemy.not_(column.contains(item)), column == negative_flag]))
            else:
                query = query.filter(sqlalchemy.not_(column.contains(item)))
        else:
            query = query.filter(column.contains(item))
    return query

def _add_or_contains_filter_(query :Select[Tuple], rq: dict, key:str, column: Tuple):
    options = [val.strip() for val in rq[key].split(",")]
    return query.filter(sqlalchemy.or_(*[column.contains(item) for item in options]))

def _get_range_lvl_(rq: dict, key: str):
    config = FOOD_SAFTY_RANGES[key]
    result : str = "low"
    for level in ["low", "middle", "high"]:
        if config[level]["start"] < rq[key] and \
                ("end" not in config[level] or rq[key] < config[level]["end"]):
            result = level
            break
    return result
