"""
Keyword Extraction Utility for Project Anima Memory System.

Extracts meaningful search keywords from raw user input text, filtering
out stopwords and short/common words, for use in memory keyword search.
"""

import re
from typing import List

STOPWORDS: set = {
    # Indonesian
    "yang", "dan", "atau", "itu", "ini", "aku", "kamu", "saya", "kita",
    "di", "ke", "dari", "untuk", "dengan", "juga", "sih", "dong", "deh",
    "ya", "nya", "ada", "ga", "gak", "nggak", "udah", "sudah", "mau",
    "bisa", "kalau", "kalo", "gimana", "kenapa", "banget", "aja",
    "tapi", "sama", "lagi", "emang", "memang", "saja", "buat", "jadi",
    "nih", "gitu", "gini", "cuma", "punya", "lain", "bikin",
    # English
    "the", "is", "and", "or", "to", "of", "a", "an", "in", "on", "for",
    "you", "i", "me", "my", "your", "hi", "hey", "hello", "want", "wanna",
    "just", "something", "about", "can", "could", "would", "please",
    "what", "why", "how", "who", "when", "where", "which", "that", "this",
    "are", "was", "were", "have", "has", "had", "will", "shall", "do",
    "did", "does", "not", "with", "from", "they", "them", "than", "its",
}


def extract_keywords(
    text: str,
    min_length: int = 4,
    max_keywords: int = 3,
) -> List[str]:
    """
    Extract meaningful keywords from a raw sentence for memory search.

    Filters out stopwords and words shorter than min_length, then returns
    up to max_keywords longest/most distinctive remaining words. Longest-first
    ordering surfaces more specific/distinctive tokens over generic short words.

    Args:
        text (str): Raw input sentence from user.
        min_length (int): Minimum character length for a word to be considered.
        max_keywords (int): Maximum number of keywords to return.

    Returns:
        List[str]: Extracted unique keywords sorted longest-first.
    """
    if not text or not text.strip():
        return []

    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    candidates = [w for w in words if len(w) >= min_length and w not in STOPWORDS]

    # Longest-first tends to surface more distinctive/specific words
    candidates.sort(key=len, reverse=True)

    # Deduplicate while preserving insertion order
    seen: set = set()
    result: List[str] = []
    for w in candidates:
        if w not in seen:
            seen.add(w)
            result.append(w)
        if len(result) >= max_keywords:
            break

    return result
