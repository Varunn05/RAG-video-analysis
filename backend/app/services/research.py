from functools import lru_cache

from tavily import TavilyClient

from ..config import get_settings


@lru_cache
def get_search_client() -> TavilyClient:
    api_key = get_settings().tavily_api_key
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured.")
    return TavilyClient(api_key=api_key)


def research_claim(claim: str) -> list[dict[str, str]]:
    response = get_search_client().search(query=claim, search_depth="advanced", max_results=5)
    return [
        {"title": item.get("title", "Untitled source"), "url": item.get("url", ""), "snippet": item.get("content", "")}
        for item in response.get("results", [])[:3]
    ]
