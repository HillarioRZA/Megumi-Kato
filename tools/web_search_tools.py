"""
Web Search Tool for Project Anima.

Provides schema definition and execution handler for the web_search tool,
which queries DuckDuckGo (no API key required) and returns a summarized
plain-text result ready for LLM consumption.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger("anima.tools.web_search")

WEB_SEARCH_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information, news, or facts that may not be "
            "in the model's training data. Use when the user asks about recent events, "
            "news, or anything that requires up-to-date information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string (e.g. 'latest AI news September 2026').",
                },
            },
            "required": ["query"],
        },
    },
}

WEB_SEARCH_TOOLS: List[Dict[str, Any]] = [WEB_SEARCH_SCHEMA]

# Maximum number of search results to include in the response
_MAX_RESULTS = 4
# Maximum characters per snippet to prevent token explosion
_MAX_SNIPPET_LENGTH = 200


def execute_web_search(query: str) -> str:
    """
    Execute a DuckDuckGo web search and return a summarized plain-text result.

    Results are limited to the top ``_MAX_RESULTS`` entries and formatted as
    numbered list items with title and truncated snippet. On any network or
    API failure, returns a descriptive error string so the model can respond
    gracefully in-character.

    Args:
        query (str): Search query string.

    Returns:
        str: Summarized search results as a readable string, or an error message.
    """
    if not query or not query.strip():
        return "Error: search query cannot be empty."

    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.error("duckduckgo-search package is not installed.")
        return "Web search tidak tersedia. Package duckduckgo-search belum terinstal."

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(
                query.strip(),
                max_results=_MAX_RESULTS,
            ))
    except Exception as exc:
        logger.warning(f"web_search failed for query='{query}': {exc}")
        return f"Pencarian gagal saat ini. Coba lagi nanti. (Error: {type(exc).__name__})"

    if not raw_results:
        return f"Tidak ditemukan hasil untuk pencarian: '{query}'"

    lines = [f"Hasil pencarian web untuk: '{query}'", ""]
    for i, item in enumerate(raw_results, start=1):
        title = item.get("title", "Tanpa judul").strip()
        snippet = item.get("body", "").strip()
        if len(snippet) > _MAX_SNIPPET_LENGTH:
            snippet = snippet[:_MAX_SNIPPET_LENGTH].rstrip() + "..."
        url = item.get("href", "")
        lines.append(f"{i}. {title}")
        if snippet:
            lines.append(f"   {snippet}")
        if url:
            lines.append(f"   URL: {url}")
        lines.append("")

    result = "\n".join(lines).strip()
    logger.info(f"web_search executed [Query: '{query}', Results: {len(raw_results)}]")
    return result
