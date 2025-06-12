from datetime import datetime, timedelta

from crunevo.extensions import db
from crunevo.models import FeedItem, Note
from crunevo.cache.feed_cache import push_items
from crunevo.utils.scoring import compute_score


def decay_scores() -> None:
    """Recalculate score for older feed items based on freshness."""
    cutoff = datetime.utcnow() - timedelta(hours=1)
    items = FeedItem.query.filter(
        FeedItem.item_type == "apunte",
        FeedItem.created_at <= cutoff,
    ).all()

    for it in items:
        note = Note.query.get(it.ref_id)
        if not note:
            continue
        it.score = compute_score(
            note.likes, note.downloads, note.comments_count, note.created_at
        )
    if items:
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
