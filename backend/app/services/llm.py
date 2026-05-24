import logging
import httpx
from ..config import settings

from app.constants import ALLERGENICS, NUTRISCORE_GRADE

logger = logging.getLogger(__name__)


async def generate_filter_using_chat(message: str, context: str) -> str:
    """Use AI to determine the best filters"""

    return await _generate_chat_reply_({
        "system_instruction": {"parts": [{"text": _build_system_prompt_filter_()}, {"text": "\n\nContext: " + context}]},
        "contents": [{"role": "user", "parts": [{"text": message}]}],
    })

async def explain_filter_using_chat(message: str, filters: str, lang:str) -> str:
    """Use AI to explain selected filters"""

    text = _build_system_prompt_explainer(filters, lang)
    return await _generate_chat_reply_({
        "system_instruction": {
            "parts": [
                {"text": _build_system_prompt_response_()},
                {"text": "\n\nContext: " + message}
            ]
        },
        "contents": [
            {"role": "user", "parts": [{"text": text}]}
        ]
    })

async def _generate_chat_reply_(payload:dict) -> str:
    if not settings.GEMINI_KEY:
        raise RuntimeError("GEMINI_KEY is not configured")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_KEY}"
    )

    try:
        async with httpx.AsyncClient(timeout=settings.GEMINI_TIMEOUT_S) as client:
            resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.exception("Gemini request failed: %s", exc)
        raise RuntimeError("Gemini request failed") from exc

    reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
    if not reply:
        raise RuntimeError("Gemini returned an empty response")
    return reply

def _language_name(lang: str) -> str:
    if lang == "ca":
        return "catalan"
    if lang == "en":
        return "english"
    return "spanish"

def _build_system_prompt_filter_() -> str:
    fields = '"nutriscore", "sugars_100g", "fat_100g", "fiber_100g", "salt_100g", "saturated-fat_100g", "dangerous_allergens"'
    nutriscore = ",".join([f'"{score}"' for score in NUTRISCORE_GRADE])
    allergens = ",".join([f'"{allergenic}"' for allergenic in ALLERGENICS])
    return (
        "You are FoodScan, an assistant specialized in finding food products.\n"
        f"You must return exactly one valid JSON object only, with these keys: {fields} and \"relevant_properties\".\n"
        "Use this exact structure and do not add any other keys or text.\n"
        f"- \"nutriscore\": string, one of {nutriscore} or null.\n"
        "  Meaning: nutritional score where \"a\" is best and \"a\" is worst.\n"
        f"- \"dangerous_allergens\": list join by comma of some of these values: {allergens}, or null.\n"
        "  Meaning: list of dangerous allergens of a food product. Use your knowledge of common allergies and medical conditions to decide which allergen is dangerous in this context. For example, if the user asks about celiacs or gluten-free products, include gluten. If the user ask for lactose intolerance, include milk\n"
        "- \"sugars_100g\": number or null.\n"
        "  Meaning: grams of sugar per 100g. Use these ranges as guidance: 0–5 = low, 5–24 = medium, greater than 24 = very high. higher values are worst\n"
        "- \"fat_100g\": number or null.\n"
        "  Meaning: grams of fat per 100g. Use these ranges as guidance: 0–3 = low, 4–18 = medium, greater than 18 = very high. higher values are worst\n"
        "- \"fiber_100g\": number or null.\n"
        "  Meaning: grams of dietary fiber per 100g. Use these ranges as guidance: 0–3 = low, 3–6 = medium, greater than 6 = very high. higher values better\n"
        "- \"salt_100g\": number or null.\n"
        "  Meaning: grams of salt per 100g. Use these ranges as guidance: 0–0.3 = low, 0.3–1.5 = medium, greater than 1.5 = very high. higher values are worst\n"
        "- \"saturated-fat_100g\": number or null.\n"
        "  Meaning: grams of saturated fat per 100g. Use these ranges as guidance: 0–1.5 = low, 1.5–5 = medium, greater than 5 = very high. higher values are worst\n"
        "- \"relevant_properties\": string.\n"
        "  Meaning: a list of properties of the object that are relevant to the question, join by comma. it can only include properties that have a logical relation to the question; only possible values are the fields listed above.\n"
        "For the fields listed above always infer a valid value\n"
        "Do not use markdown, code fences, comments, or any explanation.\n"
        "Only output the JSON object.\n"
        "Example: {\"nutriscore\": \"b\", \"sugars_100g\": 12, \"fat_100g\": 8, \"fiber_100g\": 4, \"salt_100g\": 0.8, \"saturated-fat_100g\": 2, \"relevant_properties\" : \"sugars_100g,fat_100g,salt_100g\", \"allergens\" : \"nuts,milk\", }.\n"
    )

def _build_system_prompt_response_() -> str:
    return (
        "You are Food explainer. Given this fields about nutritional information as a context:\n"
        "- \"nutriscore\": nutritional score where \"a\" is best and \"a\" is worst.\n"
        "- \"dangerous_allergens\": list of food allergens. Use your knowledge of common allergies and medical conditions to explain this. For example, if value includes gluten then info a bout celiacs is important. if value includes milk then lactose intolerance info is important\n"
        "- \"sugars_100g\": grams of sugar per 100g. Use these ranges as guidance: 0–5 = low, 5–24 = medium, greater than 24 = very high. higher values are worst\n"
        "- \"fat_100g\": grams of fat per 100g. Use these ranges as guidance: 0–3 = low, 4–18 = medium, greater than 18 = very high. higher values are worst\n"
        "- \"fiber_100g\": grams of dietary fiber per 100g. Use these ranges as guidance: 0–3 = low, 3–6 = medium, greater than 6 = very high. higher values better\n"
        "- \"salt_100g\": grams of salt per 100g. Use these ranges as guidance: 0–0.3 = low, 0.3–1.5 = medium, greater than 1.5 = very high. higher values are worst\n"
        "- \"saturated-fat_100g\": grams of saturated fat per 100g. Use these ranges as guidance: 0–1.5 = low, 1.5–5 = medium, greater than 5 = very high. higher values are worst\n"
        "- \"relevant_properties\": list of properties, about the properties previously mentioned, that are relevant to the question. if a property does not appears here, do not use it in the answer \n"
        "If the user ask for nutritional information explain it in natural language, but use a formal tone and your knowledge of nutrional data and medical information.\n"
    )

def _build_system_prompt_explainer(filters: str, lang:str) -> str:
    return (
        "for the previous question, "
        "you have determined this is the best nutritional information to filter products:\n"
        f"{filters}\n"
        "format the answer in a more user friendly format, then explain why.\n"
        "Example:\n"
        " - this is the best search for your needs:\n"
        "   - dangerous_allergens: milk.\n"
        "   the reason for this search is: lactose intolerant can not consume milk\n"
        "Rules:\n"
        " - do not use the format of the example, but it is mandatory to include the same kind of information\n"
        " - when referencing a filter, you must use user friendly words. Example: instead of \"dangerous_allergens\" use \"Dangerous Allergens\"\n"
        " - clearly indicate to the user that products list is already filtered\n"
        " - be concise\n"
        f" - reply in {_language_name(lang)}"
    )