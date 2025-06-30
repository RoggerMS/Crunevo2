import os
import time
import logging
import redis

log = logging.getLogger(__name__)

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

ATTEMPT_PREFIX = "login_attempts:"
BLOCK_LIMIT = 5
BLOCK_TTL = 15 * 60  # 15 minutes

_fallback = {}


def _client():
    from redis.exceptions import RedisError

    try:
        r.ping()
        return r
    except RedisError as exc:  # pragma: no cover - fakeredis won't hit
        log.warning("Redis ping failed – using memory cache: %s", exc)
        return None


def record_fail(username: str) -> int:
    """Increase failed attempts for username and return current count."""
    cli = _client()
    key = ATTEMPT_PREFIX + username
    if cli:
        try:
            attempts = cli.incr(key)
            if attempts == 1:
                cli.expire(key, BLOCK_TTL)
            return int(attempts)
        except redis.RedisError:
            pass
    now = time.time()
    count, expiry = _fallback.get(username, (0, now + BLOCK_TTL))
    if now > expiry:
        count, expiry = 0, now + BLOCK_TTL
    count += 1
    _fallback[username] = (count, expiry)
    return count


def reset(username: str) -> None:
    """Clear stored attempts for user."""
    cli = _client()
    key = ATTEMPT_PREFIX + username
    if cli:
        try:
            cli.delete(key)
        except redis.RedisError:
            pass
    _fallback.pop(username, None)


def get_attempts(username: str) -> int:
    cli = _client()
    key = ATTEMPT_PREFIX + username
    if cli:
        try:
            val = cli.get(key)
            return int(val) if val else 0
        except redis.RedisError:
            pass
    if username in _fallback:
        count, expiry = _fallback[username]
        if time.time() > expiry:
            del _fallback[username]
            return 0
        return count
    return 0


def get_remaining(username: str) -> int:
    cli = _client()
    key = ATTEMPT_PREFIX + username
    if cli:
        try:
            ttl = cli.ttl(key)
            return max(ttl, 0)
        except redis.RedisError:
            pass
    if username in _fallback:
        _, expiry = _fallback[username]
        rem = int(expiry - time.time())
        if rem < 0:
            del _fallback[username]
            return 0
        return rem
    return 0


def is_blocked(username: str) -> bool:
    return get_attempts(username) >= BLOCK_LIMIT
