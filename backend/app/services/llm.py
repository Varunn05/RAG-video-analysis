import json
import re
from functools import lru_cache

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from ..config import get_settings


@lru_cache
def get_llm() -> ChatGroq:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)


def _json_from_response(content: str, fallback: object) -> object:
    """Handle providers that wrap their otherwise-valid JSON in Markdown."""
    match = re.search(r"(\[.*\]|\{.*\})", content, re.DOTALL)
    if not match:
        return fallback
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return fallback


def _normalize_timestamp(value: object) -> str:
    """Return seconds from caption markers such as ``[83.42s]`` or ``01:23``."""
    raw = str(value).strip()
    bracketed = re.search(r"\[\s*([^\]]+)\s*\]", raw)
    if bracketed:
        raw = bracketed.group(1)

    clock = re.fullmatch(r"(\d+):(\d{1,2})(?::(\d{1,2}))?", raw)
    if clock:
        first, second, third = clock.groups()
        seconds = int(first) * 60 + int(second) if third is None else int(first) * 3600 + int(second) * 60 + int(third)
        return str(seconds)

    numeric = re.search(r"-?\d+(?:\.\d+)?", raw)
    return numeric.group(0) if numeric else "0"


def extract_claims(transcript: str, max_chars: int = 20_000) -> list[dict[str, str]]:
    chunks = [transcript[index:index + max_chars] for index in range(0, len(transcript), max_chars)]
    prompt = (
        "Extract verifiable factual claims from this video transcript. Return only a JSON array "
        "of objects with string keys `time` and `claim`. Use the timestamp at the start of a "
        "transcript sentence. Omit opinions, promotions, and calls to action. Combine related facts."
    )
    claims: list[dict[str, str]] = []
    for chunk in chunks:
        response = get_llm().invoke([SystemMessage(content=prompt), HumanMessage(content=chunk)])
        parsed = _json_from_response(str(response.content), [])
        if isinstance(parsed, list):
            claims.extend(
                {"time": _normalize_timestamp(item.get("time", "0")), "claim": str(item["claim"])}
                for item in parsed
                if isinstance(item, dict) and item.get("claim")
            )
    return claims


def judge_claim(claim: str, evidence_text: str) -> dict[str, str]:
    prompt = (
        "You are a careful fact checker. Judge the claim using only supplied evidence. "
        "Return only JSON: {\"verdict\": \"TRUE|FALSE|MISLEADING|UNVERIFIABLE\", "
        "\"confidence\": \"HIGH|MEDIUM|LOW\", \"explanation\": \"...\"}."
    )
    response = get_llm().invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=f"CLAIM:\n{claim}\n\nEVIDENCE:\n{evidence_text}"),
    ])
    parsed = _json_from_response(str(response.content), {})
    parsed = parsed if isinstance(parsed, dict) else {}
    verdict = str(parsed.get("verdict", "UNVERIFIABLE")).upper()
    confidence = str(parsed.get("confidence", "LOW")).upper()
    return {
        "verdict": verdict if verdict in {"TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE"} else "UNVERIFIABLE",
        "confidence": confidence if confidence in {"HIGH", "MEDIUM", "LOW"} else "LOW",
        "explanation": str(parsed.get("explanation", "Insufficient evidence to verify this claim.")),
    }
