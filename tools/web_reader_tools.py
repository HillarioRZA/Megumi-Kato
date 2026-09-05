"""
Web Reader Tool for Project Anima.

Provides schema definition and execution handler for the read_web_page tool,
which fetches and extracts clean plain text content from a specified web URL.
"""

import logging
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("anima.tools.web_reader")

READ_WEB_PAGE_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_web_page",
        "description": (
            "Fetch and extract clean readable text from a specific webpage URL. "
            "Use this tool as a follow-up when web_search snippets are not detailed enough "
            "or when you need to read the full content of an article or news page."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The target HTTP or HTTPS URL to read.",
                }
            },
            "required": ["url"],
        },
    },
}

WEB_READER_TOOLS: List[Dict[str, Any]] = [READ_WEB_PAGE_SCHEMA]

MAX_TEXT_LENGTH: int = 3000
DEFAULT_TIMEOUT: int = 10


def execute_read_web_page(url: str) -> str:
    """
    Fetch raw HTML from a URL, clean irrelevant elements (scripts/styles),
    and extract formatted plain text up to MAX_TEXT_LENGTH characters.

    Args:
        url (str): Target webpage URL to fetch.

    Returns:
        str: Extracted plain text or an informative error message.
    """
    if not url or not isinstance(url, str):
        logger.warning("Invalid or empty URL provided to read_web_page.")
        return "Error: URL must be a valid non-empty string."

    clean_url = url.strip()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        clean_url = f"https://{clean_url}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        logger.info(f"Fetching URL content: {clean_url}")
        response = requests.get(clean_url, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()

        # Parse HTML and strip non-text elements
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            element.decompose()

        # Extract text from main structural elements
        paragraphs = soup.find_all(["p", "h1", "h2", "h3", "article", "section"])
        extracted_chunks: List[str] = [
            p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
        ]

        if not extracted_chunks:
            # Fallback to general page text if no targeted paragraphs found
            raw_text = soup.get_text(separator=" ", strip=True)
            extracted_chunks = [raw_text] if raw_text else []

        full_text = "\n\n".join(extracted_chunks)

        if not full_text:
            logger.warning(f"No readable text extracted from: {clean_url}")
            return f"Webpage at {clean_url} was fetched successfully, but no readable text content was found."

        # Truncate text if it exceeds maximum allowable context window budget
        if len(full_text) > MAX_TEXT_LENGTH:
            full_text = full_text[:MAX_TEXT_LENGTH] + "\n\n[Content truncated due to length limits...]"

        logger.info(f"Successfully extracted {len(full_text)} characters from {clean_url}.")
        return f"Content from {clean_url}:\n\n{full_text}"

    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred while attempting to reach {clean_url}")
        return f"Error: Request timed out while trying to reach {clean_url}."
    except requests.exceptions.RequestException as exc:
        logger.error(f"HTTP request error for {clean_url}: {exc}")
        return f"Error: Unable to fetch content from {clean_url}. ({type(exc).__name__})"
    except Exception as exc:
        logger.error(f"Unexpected error parsing {clean_url}: {exc}")
        return f"Error: Failed to process webpage content. Details: {exc}"