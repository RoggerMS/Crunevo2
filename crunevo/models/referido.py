from datetime import datetime
from crunevo.extensions import db


class Referral(db.Model):
    __tablename__ = "referrals"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    referrer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    completado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    invitador = db.relationship("User", foreign_keys=[invitador_id])
    invitado = db.relationship("User", foreign_keys=[invitado_id])
