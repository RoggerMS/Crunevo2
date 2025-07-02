import time
import logging

log = logging.getLogger(__name__)

TTL = 90  # seconds

_fallback: dict[int, float] = {}


def mark_online(user_id: int) -> None:
    _fallback[user_id] = time.time() + TTL


def get_active_ids() -> list[int]:
    now = time.time()
    expired = [uid for uid, exp in _fallback.items() if exp < now]
    for uid in expired:
        _fallback.pop(uid, None)
    return list(_fallback.keys())
