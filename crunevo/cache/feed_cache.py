from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

log = __import__("logging").getLogger(__name__)
# simple in-memory cache keyed by user_id
_cache: dict[int, list[dict]] = defaultdict(list)

MAX_CACHE = 500  # keep most recent items
CACHE_TTL = 600  # expire items after 10 minutes

# TODO: consider using Redis with per-user TTL for distributed environments.


def push_items(user_id: int, items: list[dict]) -> None:
    """Store feed items for a user in memory sorted by score and timestamp."""
    now = datetime.utcnow()
    entries = _cache[user_id]
    entries.extend({**it, "cached_at": now} for it in items)
    entries.sort(
        key=lambda it: it["score"] + it["created_at"].timestamp() / 1e6,
        reverse=True,
    )
    cleanup_user(user_id, now)
    del entries[MAX_CACHE:]


def fetch(user_id: int, start: int = 0, stop: int = 19) -> list[dict]:
    cleanup_user(user_id)
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


def cleanup_user(user_id: int, now: Optional[datetime] = None) -> None:
    now = now or datetime.utcnow()
    cutoff = now - timedelta(seconds=CACHE_TTL)
    entries = _cache.get(user_id, [])
    _cache[user_id] = [it for it in entries if it["cached_at"] >= cutoff]
    if not _cache[user_id]:
        _cache.pop(user_id, None)


def cleanup(now: Optional[datetime] = None) -> None:
    """Clean up expired items for all users."""
    now = now or datetime.utcnow()
    for uid in list(_cache.keys()):
        cleanup_user(uid, now)


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
