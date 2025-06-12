import os
import json
import logging
import redis

log = logging.getLogger(__name__)

r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

FEED_KEY = "feed:{user_id}"
MAX_CACHE = 200  # keep most recent N items per user


def _client():
    """Return Redis client if available, otherwise ``None``."""
    from redis.exceptions import RedisError

    try:
        r.ping()
        return r
    except RedisError as exc:  # pragma: no cover - fakeredis won't hit
        log.warning("Redis ping failed – working degraded: %s", exc)
        return None


def push_items(user_id, items):
    """Store feed items for a user in Redis sorted set."""
    cli = _client()
    if not cli:
        return
    with cli.pipeline() as p:
        for it in items:
            zscore = it["score"] + it["created_at"].timestamp() / 1e6
            p.zadd(
                FEED_KEY.format(user_id=user_id), {json.dumps(it["payload"]): zscore}
            )
        # scores ascend; remove older ranks to keep only MAX_CACHE recent items
        p.zremrangebyrank(FEED_KEY.format(user_id=user_id), 0, -(MAX_CACHE + 1))
        p.expire(FEED_KEY.format(user_id=user_id), 60 * 60 * 24 * 7)
        p.execute()


def fetch(user_id, start=0, stop=19):
    cli = _client()
    if not cli:
        return []
    res = cli.zrevrange(FEED_KEY.format(user_id=user_id), start, stop)
    if log.isEnabledFor(logging.DEBUG):
        if res:
            log.debug("feed cache HIT %s %s-%s", user_id, start, stop)
        else:
            log.debug("feed cache MISS %s %s-%s", user_id, start, stop)
    return [json.loads(x) for x in res]
