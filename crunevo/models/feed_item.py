from datetime import datetime
from crunevo.extensions import db
from sqlalchemy import Enum as SAEnum, desc
import json


class FeedItem(db.Model):
    __tablename__ = "feed_item"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_type = db.Column(
        SAEnum(
            "apunte",
            "post",
            "logro",
            "evento",
            "movimiento",
            "mensaje",
            name="feed_item_type",
        ),
        nullable=False,
    )
    ref_id = db.Column(db.Integer, nullable=False)
    is_highlight = db.Column(db.Boolean, default=False)
    _metadata = db.Column("metadata", db.Text, nullable=True)
    score = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    from crunevo.models.post import Post
    from crunevo.models.note import Note

    post = db.relationship(
        "Post",
        primaryjoin="and_(FeedItem.item_type=='post', foreign(FeedItem.ref_id)==Post.id)",
        viewonly=True,
        uselist=False,
    )

    note = db.relationship(
        "Note",
        primaryjoin="and_(FeedItem.item_type=='apunte', foreign(FeedItem.ref_id)==Note.id)",
        viewonly=True,
        uselist=False,
    )

    __table_args__ = (
        db.Index(
            "idx_feed_owner_score",
            "owner_id",
            desc("score"),
            desc("created_at"),
        ),
        db.Index("idx_feed_type_ref", "item_type", "ref_id"),
    )

    def to_dict(self):
        """Return minimal data per item type for API.

        'apunte': title, summary, author_username, downloads
        'post': content, author_username, file_url
        others: fields from metadata
        """
        try:
            data = {
                "item_type": self.item_type,
                "ref_id": self.ref_id,
                "is_highlight": self.is_highlight,
            }

            meta_data = None
            if self.metadata:
                try:
                    meta_data = json.loads(self.metadata)
                except Exception:
                    meta_data = None

            if self.item_type == "apunte":
                from crunevo.models import Note, User

                note = (
                    db.session.query(
                        Note.title,
                        Note.description,
                        User.username,
                        Note.downloads,
                    )
                    .join(User, Note.user_id == User.id)
                    .filter(Note.id == self.ref_id)
                    .first()
                )
                if note:
                    data.update(
                        {
                            "title": note.title,
                            "summary": note.description,
                            "author_username": note.username,
                            "downloads": note.downloads,
                        }
                    )
                else:
                    return {"item_type": "deleted"}
            elif self.item_type == "post":
                from crunevo.models import Post, User

                post = (
                    db.session.query(Post.content, Post.file_url, User.username)
                    .join(User, Post.author_id == User.id)
                    .filter(Post.id == self.ref_id)
                    .first()
                )
                if post:
                    data.update(
                        {
                            "content": post.content,
                            "author_username": post.username,
                            "file_url": post.file_url,
                        }
                    )
                else:
                    return {"item_type": "deleted"}
            else:
                if meta_data:
                    data.update(meta_data)
            return data
        except Exception:
            return {"item_type": "deleted"}


# expose metadata attribute without conflicting with SQLAlchemy base
def _get_metadata(self):
    return self._metadata


def _set_metadata(self, value):
    self._metadata = value


FeedItem.metadata = property(_get_metadata, _set_metadata)
