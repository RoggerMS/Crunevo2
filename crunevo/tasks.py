import os
import logging
import json

from redis import Redis, RedisError
from rq import Queue

from .extensions import db
from .models import User, FeedItem, Note
from .cache.feed_cache import push_items
from .utils.scoring import compute_score

log = logging.getLogger(__name__)

# Redis connection and queue with graceful fallback
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_conn = Redis.from_url(REDIS_URL)
    redis_conn.ping()
    task_queue = Queue("crunevo", connection=redis_conn)
except RedisError as exc:  # pragma: no cover - requires no redis server
    log.warning("Redis ping failed – using local queue: %s", exc)

    class _LocalQueue:
        """Synchronous fallback when Redis is unavailable."""

        def enqueue(self, func, *args, **kwargs):
            return func(*args, **kwargs)

    redis_conn = None
    task_queue = _LocalQueue()


def insert_feed_items(
    item_type, ref_id, meta_dict=None, owner_ids=None, is_highlight=False
):
    """Insert feed items into the database and cache."""
    if owner_ids is None:
        owner_ids = [u.id for u in User.query.with_entities(User.id).all()]

    meta_str = json.dumps(meta_dict) if meta_dict else None

    base_score = 0
    if item_type == "apunte":
        note = Note.query.get(ref_id)
        if note:
            base_score = compute_score(
                note.likes, note.downloads, note.comments_count, note.created_at
            )

    items = [
        FeedItem(
            owner_id=uid,
            item_type=item_type,
            ref_id=ref_id,
            metadata=meta_str,
            is_highlight=is_highlight,
            score=base_score,
        )
        for uid in owner_ids
    ]
    if items:
        db.session.add_all(items)
        db.session.commit()
        if item_type != "apunte":
            for it in items:
                push_items(
                    it.owner_id,
                    [
                        {
                            "score": it.score,
                            "created_at": it.created_at,
                            "payload": it.to_dict(),
                        }
                    ],
                )
