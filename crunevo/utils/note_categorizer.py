import re
from typing import Iterable, List

CATEGORY_KEYWORDS = {
    "matemática": ["algebra", "geometría", "cálculo"],
    "historia": ["historia", "batalla", "guerra", "civilización"],
    "biología": ["biología", "célula", "genética"],
    "comunicación": ["comunicación", "gramática", "lenguaje"],
}


def suggest_categories(text: str, categories: Iterable[str]) -> List[str]:
    """Return likely categories for the given text."""
    if not text:
        return []
    text = text.lower()
    words = set(re.findall(r"\w+", text))
    suggestions = []
    for cat in categories:
        ckey = cat.lower()
        if ckey in text:
            suggestions.append(cat)
            continue
        for kw in CATEGORY_KEYWORDS.get(ckey, []):
            if kw in words:
                suggestions.append(cat)
                break
    # Preserve original order and limit to 3 suggestions
    seen = set()
    ordered = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            ordered.append(s)
        if len(ordered) >= 3:
            break
    return ordered
