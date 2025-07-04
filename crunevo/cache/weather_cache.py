import time
from typing import Any

TTL = 600  # 10 minutes

_cache: dict[str, tuple[Any, float]] = {}


def get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and entry[1] > time.time():
        return entry[0]
    return None


def set(key: str, data: Any) -> None:
    _cache[key] = (data, time.time() + TTL)
