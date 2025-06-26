from datetime import datetime
from crunevo.extensions import db


class PostReaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "post_id", name="uniq_post_reaction"),
    )

    @staticmethod
    def counts_for_posts(post_ids):
        if not post_ids:
            return {}
        rows = (
            db.session.query(
                PostReaction.post_id, PostReaction.reaction_type, db.func.count()
            )
            .filter(PostReaction.post_id.in_(post_ids))
            .group_by(PostReaction.post_id, PostReaction.reaction_type)
            .all()
        )
        counts = {}
        for pid, rt, cnt in rows:
            counts.setdefault(pid, {})[rt] = cnt
        return counts

    @staticmethod
    def count_for_post(post_id):
        return PostReaction.counts_for_posts([post_id]).get(post_id, {})
