"""DuckDB product store"""

import math
import re
import sqlalchemy
from sqlalchemy import func, select, text, create_engine
from sqlalchemy.orm import Session

from .config import settings
from .models import ProducDuckDB
from .constants import FOOD_SAFTY_RANGES, NUTRISCORE_GRADE

# Country → (lat, lon) centroids
_COUNTRY_COORDS: dict[str, tuple[float, float]] = {
    "spain": (40.4168, -3.7038),
    "españa": (40.4168, -3.7038),
    "france": (46.2276, 2.2137),
    "italia": (41.8719, 12.5674),
    "italy": (41.8719, 12.5674),
    "germany": (51.1657, 10.4515),
    "alemania": (51.1657, 10.4515),
    "argentina": (-34.6037, -58.3816),
    "mexico": (23.6345, -102.5528),
    "méxico": (23.6345, -102.5528),
    "united states": (37.0902, -95.7129),
    "usa": (37.0902, -95.7129),
    "us": (37.0902, -95.7129),
    "china": (35.8617, 104.1954),
    "netherlands": (52.3676, 4.9041),
    "holanda": (52.3676, 4.9041),
    "belgium": (50.8503, 4.3517),
    "bélgica": (50.8503, 4.3517),
    "portugal": (39.3999, -8.2245),
    "brazil": (-14.235, -51.9253),
    "brasil": (-14.235, -51.9253),
    "peru": (-9.19, -75.0152),
    "perú": (-9.19, -75.0152),
    "colombia": (4.5709, -74.2973),
    "chile": (-35.6751, -71.543),
    "ecuador": (-1.8312, -78.1834),
    "morocco": (31.7917, -7.0926),
    "marruecos": (31.7917, -7.0926),
    "turkey": (38.9637, 35.2433),
    "turquía": (38.9637, 35.2433),
    "india": (20.5937, 78.9629),
    "thailand": (15.87, 100.9925),
    "tailandia": (15.87, 100.9925),
    "japan": (36.2048, 138.2529),
    "japón": (36.2048, 138.2529),
    "united kingdom": (55.3781, -3.436),
    "uk": (55.3781, -3.436),
    "gran bretaña": (55.3781, -3.436),
    "poland": (51.9194, 19.1451),
    "polonia": (51.9194, 19.1451),
    "austria": (47.5162, 14.5501),
    "switzerland": (46.8182, 8.2275),
    "suiza": (46.8182, 8.2275),
    "sweden": (60.1282, 18.6435),
    "suecia": (60.1282, 18.6435),
    "denmark": (56.2639, 9.5018),
    "dinamarca": (56.2639, 9.5018),
    "greece": (39.0742, 21.8243),
    "grecia": (39.0742, 21.8243),
    "hungary": (47.1625, 19.5033),
    "hungría": (47.1625, 19.5033),
    "czech republic": (49.8175, 15.473),
    "república checa": (49.8175, 15.473),
    "romania": (45.9432, 24.9668),
    "rumanía": (45.9432, 24.9668),
    "ukraine": (48.3794, 31.1656),
    "ucrania": (48.3794, 31.1656),
    "russia": (61.524, 105.3188),
    "rusia": (61.524, 105.3188),
    "vietnam": (14.0583, 108.2772),
    "indonesia": (-0.7893, 113.9213),
    "sri lanka": (7.8731, 80.7718),
    "kenya": (-0.0236, 37.9062),
    "kenia": (-0.0236, 37.9062),
    "south africa": (-30.5595, 22.9375),
    "sudáfrica": (-30.5595, 22.9375),
    "ethiopia": (9.145, 40.4897),
    "etiopía": (9.145, 40.4897),
    "ghana": (7.9465, -1.0232),
    "ivory coast": (7.54, -5.5471),
    "côte d'ivoire": (7.54, -5.5471),
    "cameroon": (3.848, 11.5021),
    "camerún": (3.848, 11.5021),
    "new zealand": (-40.9006, 174.886),
    "nueva zelanda": (-40.9006, 174.886),
    "australia": (-25.2744, 133.7751),
    "canada": (56.1304, -106.3468),
    "canadá": (56.1304, -106.3468),
    "bolivia": (-16.2902, -63.5887),
    "venezuela": (6.4238, -66.5897),
    "paraguay": (-23.4425, -58.4438),
    "uruguay": (-32.5228, -55.7658),
    "cuba": (21.5218, -77.7812),
    "dominican republic": (18.7357, -70.1627),
    "república dominicana": (18.7357, -70.1627),
    "guatemala": (15.7835, -90.2308),
    "costa rica": (9.7489, -83.7534),
    "honduras": (15.1999, -86.2419),
    "el salvador": (13.7942, -88.8965),
    "nicaragua": (12.8654, -85.2072),
    "panama": (8.538, -80.7821),
    "panamá": (8.538, -80.7821),
    "jordan": (30.5852, 36.2384),
    "jordania": (30.5852, 36.2384),
    "israel": (31.0461, 34.8516),
    "egypt": (26.8206, 30.8025),
    "egipto": (26.8206, 30.8025),
    "iran": (32.4279, 53.688),
    "irán": (32.4279, 53.688),
    "pakistan": (30.3753, 69.3451),
    "pakistán": (30.3753, 69.3451),
    "myanmar": (21.9162, 95.956),
    "cambodia": (12.5657, 104.991),
    "taiwan": (23.6978, 120.9605),
    "south korea": (35.9078, 127.7669),
    "corea del sur": (35.9078, 127.7669),
    "philippines": (12.8797, 121.774),
    "filipinas": (12.8797, 121.774),
    "malaysia": (4.2105, 101.9758),
    "malasia": (4.2105, 101.9758),
    "singapore": (1.3521, 103.8198),
    "singapur": (1.3521, 103.8198),
}

# Spanish region/city → (lat, lon)
_SPAIN_PLACES: dict[str, tuple[float, float]] = {
    "madrid": (40.4168, -3.7038),
    "barcelona": (41.3851, 2.1734),
    "valencia": (39.4699, -0.3763),
    "sevilla": (37.3891, -5.9845),
    "seville": (37.3891, -5.9845),
    "zaragoza": (41.6488, -0.8891),
    "málaga": (36.7213, -4.4214),
    "malaga": (36.7213, -4.4214),
    "murcia": (37.9922, -1.1307),
    "palma": (39.5696, 2.6502),
    "las palmas": (28.1248, -15.43),
    "bilbao": (43.263, -2.935),
    "alicante": (38.3452, -0.4815),
    "córdoba": (37.8882, -4.7794),
    "cordoba": (37.8882, -4.7794),
    "valladolid": (41.6523, -4.7245),
    "vigo": (42.2406, -8.7207),
    "gijón": (43.5322, -5.6611),
    "gijon": (43.5322, -5.6611),
    "hospitalet": (41.3597, 2.1098),
    "granada": (37.1773, -3.5986),
    "vitoria": (42.8467, -2.6716),
    "vitoria-gasteiz": (42.8467, -2.6716),
    "elche": (38.267, -0.6981),
    "oviedo": (43.3614, -5.8593),
    "badalona": (41.4501, 2.247),
    "cartagena": (37.6257, -0.9966),
    "terrassa": (41.5625, 2.0097),
    "jerez": (36.6864, -6.1375),
    "sabadell": (41.5433, 2.1093),
    "santa cruz": (28.4636, -16.2518),
    "pamplona": (42.8125, -1.6458),
    "iruña": (42.8125, -1.6458),
    "almería": (36.8381, -2.4597),
    "almeria": (36.8381, -2.4597),
    "fuenlabrada": (40.2838, -3.7997),
    "leganés": (40.3289, -3.7639),
    "leganes": (40.3289, -3.7639),
    "donostia": (43.3128, -1.9745),
    "san sebastián": (43.3128, -1.9745),
    "san sebastian": (43.3128, -1.9745),
    "burgos": (42.3439, -3.6969),
    "santander": (43.4623, -3.8099),
    "albacete": (38.9943, -1.8585),
    "castellón": (39.9864, -0.0513),
    "castellon": (39.9864, -0.0513),
    "alcorcón": (40.3448, -3.8233),
    "alcorcon": (40.3448, -3.8233),
    "getafe": (40.3059, -3.7326),
    "logroño": (42.4627, -2.4449),
    "logrono": (42.4627, -2.4449),
    "badajoz": (38.8794, -6.9706),
    "salamanca": (40.9701, -5.6635),
    "huelva": (37.2614, -6.9447),
    "tarragona": (41.1189, 1.2445),
    "lleida": (41.6175, 0.6206),
    "lérida": (41.6175, 0.6206),
    "lerida": (41.6175, 0.6206),
    "jaén": (37.7796, -3.7849),
    "jaen": (37.7796, -3.7849),
    "torrejón": (40.4587, -3.4834),
    "mataró": (41.5396, 2.4462),
    "mataro": (41.5396, 2.4462),
    "alcalá": (40.4823, -3.3639),
    "alcala": (40.4823, -3.3639),
    "marbella": (36.5101, -4.8825),
    "lugo": (43.0097, -7.5567),
    "ourense": (42.3401, -7.8644),
    "pontevedra": (42.4298, -8.6446),
    "a coruña": (43.3623, -8.4115),
    "coruña": (43.3623, -8.4115),
    "corunna": (43.3623, -8.4115),
    "ferrol": (43.4842, -8.2319),
    "palencia": (42.0097, -4.5288),
    "ávila": (40.6559, -4.6976),
    "avila": (40.6559, -4.6976),
    "segovia": (40.9429, -4.1088),
    "cuenca": (40.0704, -2.1374),
    "guadalajara": (40.6326, -3.1649),
    "toledo": (39.8581, -4.0226),
    "ciudad real": (38.9848, -3.9274),
    "cáceres": (39.4753, -6.3724),
    "caceres": (39.4753, -6.3724),
    "mérida": (38.9181, -6.3415),
    "merida": (38.9181, -6.3415),
    "cádiz": (36.527, -6.2885),
    "cadiz": (36.527, -6.2885),
    "algeciras": (36.1408, -5.4546),
    "linares": (38.0929, -3.6356),
    "ubeda": (38.0122, -3.3703),
    "reus": (41.1557, 1.1065),
    "girona": (41.9794, 2.8214),
    "gerona": (41.9794, 2.8214),
    "manresa": (41.7286, 1.8214),
    "vic": (41.9298, 2.2551),
    "olot": (42.1821, 2.489),
    "figueres": (42.2666, 2.9636),
    "sitges": (41.2367, 1.8157),
    "igualada": (41.5791, 1.619),
    "gandía": (38.9644, -0.1797),
    "benidorm": (38.5401, -0.1226),
    "torrevieja": (37.9781, -0.6839),
    "elda": (38.4791, -0.7948),
    "orihuela": (38.0836, -0.9485),
    "xàtiva": (38.99, -0.5186),
    "alcira": (39.1499, -0.4348),
    "requena": (39.4888, -1.0999),
    "alzira": (39.1499, -0.4348),
    "manacor": (39.5681, 3.2086),
    "inca": (39.7197, 2.9106),
    "mahón": (39.8929, 4.2664),
    "maó": (39.8929, 4.2664),
    "ciutadella": (39.9993, 3.8309),
    "eivissa": (38.9088, 1.4328),
    "ibiza": (38.9088, 1.4328),
    "arona": (28.0997, -16.6803),
    "telde": (27.9995, -15.4168),
    "torremolinos": (36.6223, -4.4994),
    "fuengirola": (36.5399, -4.6237),
    "vélez": (36.7833, -4.0999),
    "antequera": (37.0186, -4.5589),
    "linares": (38.0929, -3.6356),
    "andújar": (38.0393, -4.0508),
    "ronda": (36.7465, -5.1655),
    "ecija": (37.5408, -5.0828),
    "utrera": (37.1852, -5.7801),
    "dos hermanas": (37.2761, -5.9219),
    "alcalá de guadaíra": (37.3379, -5.8412),
    "el ejido": (36.777, -2.8157),
    "roquetas": (36.7635, -2.6148),
    "almería": (36.8381, -2.4597),
    "andorra": (42.5063, 1.5218),
    "cataluña": (41.5912, 1.5209),
    "catalonia": (41.5912, 1.5209),
    "andalucía": (37.5443, -4.7278),
    "andalucia": (37.5443, -4.7278),
    "castilla": (41.6523, -4.7245),
    "extremadura": (39.4937, -6.0679),
    "galicia": (42.5751, -8.1339),
    "asturias": (43.3614, -5.8593),
    "cantabria": (43.1828, -3.9875),
    "navarra": (42.6954, -1.6761),
    "navarre": (42.6954, -1.6761),
    "aragón": (41.5976, -0.9057),
    "aragon": (41.5976, -0.9057),
    "la rioja": (42.2871, -2.5396),
    "rioja": (42.2871, -2.5396),
    "murcia region": (37.9922, -1.1307),
    "baleares": (39.6953, 3.0176),
    "canarias": (28.2916, -15.6291),
    "canary islands": (28.2916, -15.6291),
    "país vasco": (43.0027, -2.6189),
    "pais vasco": (43.0027, -2.6189),
    "basque country": (43.0027, -2.6189),
    "euskadi": (43.0027, -2.6189),
    "lorqui": (38.0786, -1.2666),
    "alguazas": (38.0587, -1.2387),
    "totana": (37.7709, -1.5019),
    "lorca": (37.6703, -1.7009),
    "cieza": (38.2395, -1.4199),
    "molina de segura": (38.0556, -1.2118),
    "alcantarilla": (37.9699, -1.2116),
    "alhama": (37.8502, -1.4265),
    "yecla": (38.6159, -1.1138),
    "jumilla": (38.4721, -1.3206),
    "caravaca": (38.1072, -1.8704),
    "calasparra": (38.2282, -1.6977),
    "ceutí": (38.0838, -1.2612),
    "ceuti": (38.0838, -1.2612),
    "bullas": (38.0472, -1.6681),
    "mula": (38.044, -1.4916),
    "mazarrón": (37.5996, -1.3164),
    "mazarron": (37.5996, -1.3164),
    "aguilas": (37.4064, -1.5826),
    "águilas": (37.4064, -1.5826),
    "puerto lumbreras": (37.5688, -1.8099),
    "caravaca de la cruz": (38.1072, -1.8704),
}

_engine_ = create_engine(f"duckdb:///{settings.DATABASE_DUCKDB}")
_con_    = Session(_engine_)

_CAT_MAP = {
    # stems chosen to match both singular and plural forms in categories_en
    "Lácteos":   ("dairi", "milk", "chees", "yogurt", "yoghurt", "cream", "butter", "kefir",
                  "whey", "lactose"),
    "Panadería": ("bread", "biscuit", "pastri", "cake", "flour", "cereal", "bakery", "pasta",
                  "noodle", "cracker", "cookie", "wafer", "toast", "muesli", "porridge",
                  "oat", "rusk", "brioche", "croissant"),
    "Bebidas":   ("beverage", "drink", "juice", "waters", "mineral water", "coffee", "tea",
                  "soda", "cola", "beer", "wine", "alcohol", "spirit", "infusion",
                  "smoothie", "shake", "lemonade", "nectar"),
}

def _display_cat(cat: str | None) -> str:
    if not cat:
        return "Alimentación"
    c = cat.lower()
    for label, keywords in _CAT_MAP.items():
        if any(k in c for k in keywords):
            return label
    return "Alimentación"


def _display_cat_expr():
    """SQL CASE WHEN expression with same priority as _display_cat()."""
    col = ProducDuckDB.cat

    def _any(keywords):
        return sqlalchemy.or_(*[col.ilike(f"%{k}%") for k in keywords])

    return sqlalchemy.case(
        (_any(_CAT_MAP["Lácteos"]),   "Lácteos"),
        (_any(_CAT_MAP["Panadería"]), "Panadería"),
        (_any(_CAT_MAP["Bebidas"]),   "Bebidas"),
        else_="Alimentación",
    )


def _get_location(p: "ProducDuckDB") -> tuple[float, float]:
    """Return (lat, lon) for a product using available location fields."""
    # 1. Packaging geo (format "lat,lon")
    if p.packaging_geo:
        try:
            parts = p.packaging_geo.split(",")
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (round(lat, 4), round(lon, 4))
        except (ValueError, IndexError):
            pass

    # 2. manufacturing_places — look for Spanish city/region names
    if p.manufacturing_places:
        tokens = [t.strip().lower() for t in re.split(r"[,/\n]+", p.manufacturing_places) if t.strip()]
        for tok in tokens:
            if tok in _SPAIN_PLACES:
                return _SPAIN_PLACES[tok]
        # partial match for compound names like "Lorqui,Murcia"
        for tok in tokens:
            for key, coords in _SPAIN_PLACES.items():
                if len(key) > 3 and key in tok:
                    return coords

    # 3. origins_en — country-level centroid
    if p.origin:
        tokens = [t.strip().lower() for t in re.split(r"[,/\n]+", p.origin) if t.strip()]
        for tok in tokens:
            clean = tok.removeprefix("en:").strip()
            if clean in _COUNTRY_COORDS:
                return _COUNTRY_COORDS[clean]
            # partial
            for key, coords in _COUNTRY_COORDS.items():
                if len(key) > 3 and key == clean:
                    return coords

    # 4. All products in our catalog are sold in Spain → use Spain centroid as fallback
    return _COUNTRY_COORDS["spain"]


def _get_location_label(p: "ProducDuckDB") -> str:
    """Return a human-readable location label (city, region or country)."""
    # 1. Spanish city from manufacturing_places
    if p.manufacturing_places:
        tokens = [t.strip() for t in re.split(r"[,/\n]+", p.manufacturing_places) if t.strip()]
        for tok in tokens:
            if tok.lower() in _SPAIN_PLACES:
                return tok.title()
        for tok in tokens:
            for key in _SPAIN_PLACES:
                if len(key) > 3 and key in tok.lower():
                    return tok.title()

    # 2. Country from origins_en
    if p.origin:
        tokens = [t.strip() for t in re.split(r"[,/\n]+", p.origin) if t.strip()]
        for tok in tokens:
            clean = tok.lower().removeprefix("en:").strip()
            if clean in _COUNTRY_COORDS:
                return tok.removeprefix("en:").strip().title()

    # 3. Fallback
    return "España"


def _grade(val: str | None) -> str | None:
    return val.strip().upper() if val and val.strip() else None


def _f(val) -> float:
    try: return round(float(val), 1)
    except: return 0.0

def _f_or_none(val) -> float | None:
    try: return round(float(val), 1) or None
    except: return None


def _clean_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [
        t.strip().removeprefix("en:").replace("-", " ").title()
        for t in raw.split(",")
        if t.strip() and t.strip() not in ("", "en:")
    ]


def _serialize(p: ProducDuckDB) -> dict:
    lat, lon = _get_location(p)
    location_label = _get_location_label(p)
    return {
        "id":             p.id or "",
        "name":           p.name or "",
        "cat":            _display_cat(p.cat),
        "origin":         location_label,
        "location_label": location_label,
        "ns":         _grade(p.ns),
        "ns2":         _grade(p.ns2),
        "es":         _grade(p.es),
        "co2":        _f_or_none(p.co2),
        "image_url":  p.image_url or None,
        "img_nut":    p.img_nutrition or None,
        "desc":       p.desc or "",
        "brand":      p.brands_en or "",
        "nova":       p.nova_group or "",
        "labels":     _clean_tags(p.labels_en),
        "allergens":  ", ".join(_clean_tags(p.allergens_en or p.allergens or "")),
        "unit":       p.unit or "",
        # nutritional per 100g
        "kcal":       _f(p.kcal_100g),
        "proteins":   _f(p.proteins_100g),
        "carbs":      _f(p.carbs_100g),
        "sugars":     _f(p.sugars_100g),
        "fat":        _f(p.fat_100g),
        "fat_sat":    _f(p.fat_sat_100g),
        "fiber":      _f(p.fiber_100g),
        "salt":       _f(p.salt_100g),
        # location
        "lat":        lat,
        "lon":        lon,
        # legacy / frontend helpers
        "bens":       [],
        "certs":      [],
        "km":         0,
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
            # NULL cat must be treated as "does not contain term" (NOT excluded)
            query = query.filter(
                sqlalchemy.or_(
                    ProducDuckDB.cat.is_(None),
                    sqlalchemy.not_(ProducDuckDB.cat.ilike(f"%{t}%")),
                )
            )

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

    if _is_relevant_(rq, "display_cat"):
        query = query.filter(_display_cat_expr() == rq["display_cat"])

    return query


class _LocProxy:
    """Lightweight stand-in for ProducDuckDB used during proximity sorting."""
    __slots__ = ("manufacturing_places", "origin", "packaging_geo")
    def __init__(self, mfg, org, geo):
        self.manufacturing_places = mfg
        self.origin = org
        self.packaging_geo = geo


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def read_products(rq: dict, page: int | None, page_size: int):
    page   = page or 1
    offset = (page - 1) * page_size

    base  = _base_query(rq)
    total = _con_.execute(select(func.count()).select_from(base.subquery())).scalar() or 0

    try:
        ulat = float(rq["user_lat"])
        ulon = float(rq["user_lon"])
        has_loc = True
    except (KeyError, TypeError, ValueError):
        has_loc = False

    if has_loc:
        # Lightweight fetch: only location columns for all matching rows
        light = base.with_only_columns(
            ProducDuckDB.id,
            ProducDuckDB.manufacturing_places,
            ProducDuckDB.origin,
            ProducDuckDB.packaging_geo,
        )
        lrows = _con_.execute(light).all()

        def _dist(r):
            lat, lon = _get_location(_LocProxy(r[1], r[2], r[3]))
            return _haversine(ulat, ulon, lat, lon)

        sorted_ids = [r[0] for r in sorted(lrows, key=_dist)]
        page_ids   = sorted_ids[offset: offset + page_size]
        id_rank    = {pid: i for i, pid in enumerate(page_ids)}

        rows = [item[0] for item in _con_.execute(
            select(ProducDuckDB).filter(ProducDuckDB.id.in_(page_ids))
        ).all()]
        rows.sort(key=lambda p: id_rank.get(p.id, 999))
    else:
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
