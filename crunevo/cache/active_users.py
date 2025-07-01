import os
import time
import logging
import redis

log = logging.getLogger(__name__)

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

KEY_PREFIX = "chat_active:"
TTL = 90  # seconds

_fallback = {}


def _client():
    from redis.exceptions import RedisError

    try:
        r.ping()
        return r
    except RedisError as exc:  # pragma: no cover - fakeredis won't hit
        log.warning("Redis ping failed – using memory cache: %s", exc)
        return None


def mark_online(user_id: int) -> None:
    cli = _client()
    if cli:
        try:
            cli.setex(KEY_PREFIX + str(user_id), TTL, 1)
            return
        except redis.RedisError:
            pass
    _fallback[user_id] = time.time() + TTL


def get_active_ids() -> list[int]:
    cli = _client()
    now = time.time()
    if cli:
        try:
            keys = cli.keys(KEY_PREFIX + "*")
            ids = [int(k.decode().split(":", 1)[1]) for k in keys]
            return ids
        except redis.RedisError:
            pass
    expired = [uid for uid, exp in _fallback.items() if exp < now]
    for uid in expired:
        _fallback.pop(uid, None)
    return list(_fallback.keys())
