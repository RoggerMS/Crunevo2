from datetime import datetime, timedelta
from flask import current_app

from crunevo.extensions import db
from crunevo.models import Post, PostComment, PostReaction, FeedItem

try:
    from crunevo.models import SavedPost
except Exception:  # pragma: no cover - optional model
    SavedPost = None


def cleanup_inactive_posts(days: int | None = None) -> None:
    """Delete posts with no interactions older than the given number of days."""
    if days is None:
        days = current_app.config.get("POST_RETENTION_DAYS", 30)
    cutoff = datetime.utcnow() - timedelta(days=days)

    posts = Post.query.filter(Post.created_at < cutoff).all()
    for post in posts:
        if (
            PostComment.query.filter_by(post_id=post.id).count() == 0
            and PostReaction.query.filter_by(post_id=post.id).count() == 0
            and (post.likes or 0) == 0
        ):
            FeedItem.query.filter_by(item_type="post", ref_id=post.id).delete()
            if SavedPost:
                SavedPost.query.filter_by(post_id=post.id).delete()
            db.session.delete(post)
    db.session.commit()
