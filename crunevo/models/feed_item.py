from datetime import datetime
from crunevo.extensions import db
from sqlalchemy import Enum

class FeedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_type = db.Column(Enum('apunte', 'post', name='feed_item_type'), nullable=False)
    ref_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {
            'item_type': self.item_type,
            'ref_id': self.ref_id,
        }
        if self.item_type == 'apunte':
            from crunevo.models import Note, User
            note = (db.session.query(Note.title, Note.description, User.username, Note.downloads)
                    .join(User, Note.user_id == User.id)
                    .filter(Note.id == self.ref_id)
                    .first())
            if note:
                data.update({
                    'title': note.title,
                    'summary': note.description,
                    'author_username': note.username,
                    'downloads': note.downloads,
                })
        elif self.item_type == 'post':
            from crunevo.models import Post, User
            post = (db.session.query(Post.content, Post.image_url, User.username)
                    .join(User, Post.user_id == User.id)
                    .filter(Post.id == self.ref_id)
                    .first())
            if post:
                data.update({
                    'content': post.content,
                    'author_username': post.username,
                    'image_url': post.image_url,
                })
        return data

