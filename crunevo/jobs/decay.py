from datetime import datetime, timedelta
import logging

from crunevo.extensions import db
from crunevo.models import FeedItem, Note
from crunevo.cache.feed_cache import push_items
from crunevo.utils.scoring import compute_score


BATCH = 1000


def decay_scores(batch_size: int = BATCH) -> None:
    """Recalculate score for older feed items based on freshness."""
    log = logging.getLogger(__name__)
    cutoff = datetime.utcnow() - timedelta(hours=1)
    base_q = FeedItem.query.filter(
        FeedItem.item_type == "apunte",
        FeedItem.created_at <= cutoff,
    ).order_by(FeedItem.created_at)

    offset = 0
    processed = 0
    while True:
        items = base_q.offset(offset).limit(batch_size).all()
        if not items:
            break
        for it in items:
            note = Note.query.get(it.ref_id)
            if not note:
                continue
            it.score = compute_score(
                note.likes, note.downloads, note.comments_count, note.created_at
            )
        db.session.commit()
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
        processed += len(items)
        offset += batch_size

    if processed:
        log.info("decay_scores: processed %d items", processed)
