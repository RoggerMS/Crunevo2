import re

BANNED_WORDS = [
    "tonto",
    "idiota",
    "imbecil",
]

_pattern = re.compile("|".join(re.escape(w) for w in BANNED_WORDS), re.IGNORECASE)


def sanitize_message(text: str) -> str:
    """Replace banned words with asterisks."""
    if not text:
        return text
    return _pattern.sub(lambda m: "*" * len(m.group()), text)
