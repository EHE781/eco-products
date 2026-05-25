import logging
import httpx
from ..config import settings
from ..constants import ALLERGENICS, NUTRISCORE_GRADE

logger = logging.getLogger(__name__)

_TABLE_SCHEMA = (
    "Table: OPENFOOD_PRODUCTS. "
    "Relevant columns: product_name, categories_en, countries_tags, nutriscore_grade, "
    "environmental_score_grade, allergens, sugars_100g, fat_100g, fiber_100g, salt_100g, "
    "\"saturated-fat_100g\", \"carbon-footprint_100g\", origins_en, image_small_url. "
    "Always filter by countries_tags LIKE '%en:spain%'."
)

_QUERY_TOOL = {
    "functionDeclarations": [{
        "name": "query_database",
        "description": (
            "Execute a read-only SQL SELECT on the product database to explore available data — "
            "e.g. what categories exist, nutritional value ranges, or which allergens appear. "
            "Use this to understand what filters make sense before calling search_products. "
            f"{_TABLE_SCHEMA}"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A valid SELECT statement. Only SELECT is allowed.",
                }
            },
            "required": ["sql"],
        },
    }]
}

_SEARCH_TOOL = {
    "functionDeclarations": [{
        "name": "search_products",
        "description": (
            "Search the local food product database using nutritional and dietary filters. "
            "Call this when the user asks about specific foods, dietary restrictions, allergies, "
            "nutritional quality, or product recommendations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": (
                        "Text search across product name and categories. "
                        "Use English or Spanish food terms (e.g. 'dairy milk yogurt', 'bread bakery pan', 'bebidas drink'). "
                        "Prefix a term with '-' to exclude it (e.g. '-food' to exclude generic food items). "
                        "Always provide this when the user mentions a specific food type or category."
                    ),
                },
                "nutriscore": {
                    "type": "string",
                    "enum": NUTRISCORE_GRADE,
                    "description": "Nutritional score filter (a=best, e=worst)",
                },
                "dangerous_allergens": {
                    "type": "string",
                    "description": (
                        f"Comma-separated allergens to exclude. Possible values: {', '.join(ALLERGENICS)}"
                    ),
                },
                "sugars_100g": {
                    "type": "number",
                    "description": "Sugar threshold per 100g — 0–5=low, 5–24=medium, >24=high",
                },
                "fat_100g": {
                    "type": "number",
                    "description": "Fat threshold per 100g — 0–3=low, 4–18=medium, >18=high",
                },
                "fiber_100g": {
                    "type": "number",
                    "description": "Fiber threshold per 100g — 0–3=low, 3–6=medium, >6=high",
                },
                "salt_100g": {
                    "type": "number",
                    "description": "Salt threshold per 100g — 0–0.3=low, 0.3–1.5=medium, >1.5=high",
                },
                "saturated-fat_100g": {
                    "type": "number",
                    "description": "Saturated fat threshold per 100g — 0–1.5=low, 1.5–5=medium, >5=high",
                },
                "relevant_properties": {
                    "type": "string",
                    "description": "Comma-separated list of the parameter names above that are relevant to this query (always include 'q' when a food type is specified)",
                },
            },
            "required": [],
        },
    }]
}


_MAX_TOOL_ROUNDS = 5  # prevent infinite loops

async def generate_chat_reply_stream(message: str, lang: str = "es", context: str = ""):
    """Async generator that yields SSE-ready dicts:
      {"type": "progress", "message": "..."}  — while tools are running
      {"type": "done", "reply": "...", "filtered": {...} | None}  — final event
    """
    from ..database_duckdb import read_products, execute_readonly_query  # avoid circular import

    contents = [{"role": "user", "parts": [{"text": message}]}]
    payload = {
        "system_instruction": {"parts": [{"text": _system_prompt(lang, context)}]},
        "contents": contents,
        "tools": [_QUERY_TOOL, _SEARCH_TOOL],
    }

    last_search: dict | None = None
    parts: list = []

    for _ in range(_MAX_TOOL_ROUNDS):
        data          = await _call_gemini(payload)
        candidate     = data.get("candidates", [{}])[0]
        model_content = candidate.get("content", {})
        parts         = model_content.get("parts", [])
        func_calls    = [p["functionCall"] for p in parts if "functionCall" in p]

        if not func_calls:
            break

        # Use the exact content Gemini returned — never reconstruct it
        contents.append(model_content)

        responses = []
        for fc in func_calls:
            name = fc.get("name")
            args = fc.get("args", {})

            yield {"type": "progress", "message": _tool_progress_msg(name, args, lang)}

            try:
                if name == "search_products":
                    last_search = read_products(args, None, 10)
                    response = {
                        "products": [_slim(p) for p in last_search.get("products", [])],
                        "count":    last_search.get("count", 0),
                    }
                elif name == "query_database":
                    rows     = execute_readonly_query(args.get("sql", ""))
                    response = {"rows": rows, "count": len(rows)}
                else:
                    response = {"error": f"Unknown tool: {name}"}
            except Exception as exc:
                logger.warning("Tool %s failed: %s", name, exc)
                response = {"error": str(exc)}

            responses.append({"functionResponse": {"name": name, "response": {"result": response}}})

        contents.append({"role": "user", "parts": responses})
        payload["contents"] = contents

    text = next((p["text"] for p in parts if "text" in p), None)

    if not text:
        payload["toolConfig"] = {"functionCallingConfig": {"mode": "NONE"}}
        data  = await _call_gemini(payload)
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text  = next((p["text"] for p in parts if "text" in p), None)

    yield {"type": "done", "reply": text or "", "filtered": last_search}


async def generate_chat_reply(message: str, lang: str = "es", context: str = "") -> tuple[str, dict | None]:
    """Non-streaming wrapper — collects the generator and returns the final result."""
    text, filtered = "", None
    async for event in generate_chat_reply_stream(message, lang, context):
        if event["type"] == "done":
            text, filtered = event["reply"], event.get("filtered")
    return text, filtered


# ── Internals ─────────────────────────────────────────────────────────────────

def _system_prompt(lang: str, context: str) -> str:
    base = (
        "You are EcoScan, a friendly assistant that helps users find ecological and sustainable "
        "food products in Barcelona. "
        "When users ask about specific foods, nutrition, allergies, dietary restrictions, or product "
        "recommendations, call the search_products tool to find relevant items. "
        "IMPORTANT: When calling search_products, ALWAYS set the 'q' parameter to describe the food type "
        "the user asked for (e.g. if they ask for dairy → q='lacteo dairy milk yogurt'; "
        "bread → q='pan bread bakery'; drinks → q='bebida drink beverage -food'). "
        "Only omit 'q' if the user has not specified any food type at all. "
        "For greetings, general conversation, or non-food topics, respond directly without calling the tool. "
        "Keep responses concise and friendly. "
        f"Always reply in {_language_name(lang)}."
    )
    return base + (f"\n\nProduct context: {context}" if context else "")


def _slim(p: dict) -> dict:
    """Return only the fields Gemini needs to generate a useful response."""
    return {k: p[k] for k in ("id", "name", "cat", "origin", "ns", "es", "co2", "desc") if k in p}


async def _call_gemini(payload: dict) -> dict:
    if not settings.GEMINI_KEY:
        raise RuntimeError("GEMINI_KEY not configured")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_KEY}"
    )
    async with httpx.AsyncClient(timeout=settings.GEMINI_TIMEOUT_S) as client:
        resp = await client.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()


def _language_name(lang: str) -> str:
    return {"ca": "Catalan", "en": "English"}.get(lang, "Spanish")


def _tool_progress_msg(name: str, args: dict, lang: str) -> str:
    _t = {
        "es": {
            "query":  "📊 Explorando la base de datos…",
            "search": "🛒 Buscando productos",
            "ns":     "Nutriscore {}",
            "alrg":   "sin alérgenos",
            "nutr":   "filtros nutricionales",
        },
        "ca": {
            "query":  "📊 Explorant la base de dades…",
            "search": "🛒 Cercant productes",
            "ns":     "Nutriscore {}",
            "alrg":   "sense al·lèrgens",
            "nutr":   "filtres nutricionals",
        },
        "en": {
            "query":  "📊 Exploring the database…",
            "search": "🛒 Searching products",
            "ns":     "Nutriscore {}",
            "alrg":   "allergen-free",
            "nutr":   "nutritional filters",
        },
    }.get(lang, {})
    _t = _t or _t.get("es", {})

    if name == "query_database":
        return _t.get("query", "📊 Querying…")

    if name == "search_products":
        rel   = args.get("relevant_properties", "") or ""
        hints = []
        if args.get("q"):
            hints.append(args["q"].replace("-", "").strip()[:30])
        if "nutriscore" in rel and args.get("nutriscore"):
            hints.append(_t.get("ns", "Nutriscore {}").format(args["nutriscore"].upper()))
        if "dangerous_allergens" in rel and args.get("dangerous_allergens"):
            hints.append(_t.get("alrg", "allergen-free"))
        if any(k in rel for k in ("sugars_100g", "fat_100g", "salt_100g", "fiber_100g", "saturated-fat_100g")):
            hints.append(_t.get("nutr", "nutritional filters"))
        base = _t.get("search", "🛒 Searching")
        return f"{base}: {', '.join(hints)}…" if hints else f"{base}…"

    return f"⚙️ {name}…"
