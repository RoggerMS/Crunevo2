import json
import os
from typing import Iterable, Dict

import requests


def _gt(text: str, lang: str) -> str:
    resp = requests.get(
        "https://translate.googleapis.com/translate_a/single",
        params={"client": "gtx", "dt": "t", "sl": "auto", "tl": lang, "q": text},
        timeout=5,
    )
    if resp.ok:
        try:
            data = resp.json()
            return "".join([t[0] for t in data[0]])
        except Exception:
            return text
    return text


def translate_fields(
    note_id: int, title: str, description: str, languages: Iterable[str], folder: str
) -> Dict[str, Dict[str, str]]:
    """Translate title and description into languages and store as JSON."""
    translations = {}
    for lang in languages:
        try:
            translations[lang] = {
                "title": _gt(title or "", lang),
                "description": _gt(description or "", lang),
            }
        except Exception:
            continue

    if translations:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{note_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
    return translations
