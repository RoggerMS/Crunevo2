from datetime import datetime
from crunevo.extensions import db
from crunevo.cache.feed_cache import push_items
from crunevo.models import FeedItem, Note

LIKE_WEIGHT = 4
DOWNLOAD_WEIGHT = 2
COMMENT_WEIGHT = 1


def compute_score(
    likes: int, downloads: int, comments: int, created: datetime
) -> float:
    """Compute ranking score for a note."""
    age_hours = (datetime.utcnow() - created).total_seconds() / 3600
    freshness = max(0.0, 1 - age_hours / 48)
    base = likes * LIKE_WEIGHT + downloads * DOWNLOAD_WEIGHT + comments * COMMENT_WEIGHT
    return base * freshness


def update_feed_score(note_id: int) -> None:
    note = Note.query.get(note_id)
    if not note:
        return
    new_score = compute_score(
        note.likes,
        note.downloads,
        note.comments_count,
        note.created_at,
    )
    feed_items = FeedItem.query.filter_by(item_type="apunte", ref_id=note_id).all()
    for fi in feed_items:
        fi.score = new_score
    if feed_items:
        db.session.commit()
        for fi in feed_items:
            push_items(
                fi.owner_id,
                [
                    {
                        "score": fi.score,
                        "created_at": fi.created_at,
                        "payload": fi.to_dict(),
                    }
                ],
            )
