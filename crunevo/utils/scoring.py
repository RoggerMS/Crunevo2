from datetime import datetime
from flask import current_app
from crunevo.extensions import db
from crunevo.cache.feed_cache import push_items
from crunevo.models import FeedItem, Note


def _weights():
    cfg = current_app.config
    return (
        cfg.get("FEED_LIKE_W", 4),
        cfg.get("FEED_DL_W", 2),
        cfg.get("FEED_COM_W", 1),
        cfg.get("FEED_HALF_LIFE_H", 24),
    )


def compute_score(
    likes: int, downloads: int, comments: int, created: datetime
) -> float:
    """Compute ranking score for a note."""
    like_w, dl_w, com_w, half_life = _weights()
    age_hours = (datetime.utcnow() - created).total_seconds() / 3600
    freshness = 1 / (1 + age_hours / half_life)
    base = likes * like_w + downloads * dl_w + comments * com_w
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
