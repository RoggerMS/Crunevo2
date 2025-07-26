from datetime import datetime
from crunevo.extensions import db


class SystemErrorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ruta = db.Column(db.String(255))
    mensaje = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    resuelto = db.Column(db.Boolean, default=False)

    user = db.relationship("User")
