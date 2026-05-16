import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


def _language_name(lang: str) -> str:
    if lang == "ca":
        return "catalan"
    if lang == "en":
        return "english"
    return "spanish"


def build_system_prompt(products: list[dict], lang: str, context: str | None = None) -> str:
    catalog = "\n".join(
        [
            f"[{p['id']}] {p['name']} | {p['cat']} | {p['origin']} | {p['km']:.1f}km | "
            f"NS:{p['ns']} ES:{p['es']} | EUR {p['price']}/{p['unit']} | CO2:{p['co2']}kg | {p['desc']}"
            for p in products
        ]
    )
    context_block = f"\nSelected product context:\n{context}" if context else ""
    return (
        "You are EcoScan, an assistant specialized in sustainable grocery shopping.\n"
        f"Current catalog:\n{catalog}"
        f"{context_block}\n"
        f"Reply in {_language_name(lang)}. Be concise and useful."
    )


def generate_chat_reply(message: str, system_prompt: str) -> str:
    if not settings.GEMINI_KEY:
        raise RuntimeError("GEMINI_KEY is not configured")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_KEY}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": message}]}],
    }

    try:
        resp = httpx.post(url, json=payload, timeout=settings.GEMINI_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.exception("Gemini request failed: %s", exc)
        raise RuntimeError("Gemini request failed") from exc

    reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
    if not reply:
        raise RuntimeError("Gemini returned an empty response")
    return reply
