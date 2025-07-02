import logging
import json

from .extensions import db
from .models import User, FeedItem, Note
from .cache.feed_cache import push_items
from .utils.scoring import compute_score

log = logging.getLogger(__name__)


# Simple synchronous queue used for task execution
class _LocalQueue:
    """Synchronous task queue."""

    def enqueue(self, func, *args, **kwargs):
        return func(*args, **kwargs)


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
