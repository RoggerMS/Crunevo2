from crunevo.extensions import db


class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    url = db.Column(db.String(255), nullable=False)
