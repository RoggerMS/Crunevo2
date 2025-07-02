import time
import logging

log = logging.getLogger(__name__)

BLOCK_LIMIT = 5
BLOCK_TTL = 15 * 60  # 15 minutes

_fallback: dict[str, tuple[int, float]] = {}


def record_fail(username: str) -> int:
    """Increase failed attempts for username and return current count."""
    now = time.time()
    count, expiry = _fallback.get(username, (0, now + BLOCK_TTL))
    if now > expiry:
        count, expiry = 0, now + BLOCK_TTL
    count += 1
    _fallback[username] = (count, expiry)
    return count


def reset(username: str) -> None:
    """Clear stored attempts for user."""
    _fallback.pop(username, None)


def get_attempts(username: str) -> int:
    now = time.time()
    if username in _fallback:
        count, expiry = _fallback[username]
        if now > expiry:
            del _fallback[username]
            return 0
        return count
    return 0


def get_remaining(username: str) -> int:
    now = time.time()
    if username in _fallback:
        _, expiry = _fallback[username]
        rem = int(expiry - now)
        if rem < 0:
            del _fallback[username]
            return 0
        return rem
    return 0


def is_blocked(username: str) -> bool:
    return get_attempts(username) >= BLOCK_LIMIT
