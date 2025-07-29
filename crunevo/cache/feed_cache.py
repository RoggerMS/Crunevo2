from collections import defaultdict

log = __import__("logging").getLogger(__name__)
# simple in-memory cache keyed by user_id
_cache: dict[int, list[dict]] = defaultdict(list)

MAX_CACHE = 500  # keep most recent items


def push_items(user_id: int, items: list[dict]) -> None:
    """Store feed items for a user in memory sorted by score and timestamp."""
    entries = _cache[user_id]
    entries.extend(items)
    entries.sort(
        key=lambda it: it["score"] + it["created_at"].timestamp() / 1e6,
        reverse=True,
    )
    del entries[MAX_CACHE:]


def fetch(user_id: int, start: int = 0, stop: int = 19) -> list[dict]:
    entries = _cache.get(user_id, [])
    sliced = entries[start : stop + 1]
    if log.isEnabledFor(__import__("logging").DEBUG):
        log.debug(
            "feed cache %s %s-%s %s",
            "HIT" if sliced else "MISS",
            user_id,
            start,
            stop,
        )
    return [it["payload"] for it in sliced]


def remove_item(user_id: int, item_type: str, ref_id: int) -> None:
    entries = _cache.get(user_id, [])
    _cache[user_id] = [
        it
        for it in entries
        if not (
            it["payload"].get("item_type") == item_type
            and it["payload"].get("ref_id") == ref_id
        )
    ]
