from datetime import datetime

from crunevo.extensions import db


class MarketplaceConversation(db.Model):
    """Modelo para agrupar conversaciones entre usuarios."""

    __tablename__ = "marketplace_conversations"

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    user1 = db.relationship("User", foreign_keys=[user1_id])
    user2 = db.relationship("User", foreign_keys=[user2_id])
    messages = db.relationship(
        "MarketplaceMessage",
        backref="conversation",
        cascade="all, delete-orphan",
        order_by="MarketplaceMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<MarketplaceConversation {self.id}>"


class MarketplaceMessage(db.Model):
    """Modelo para mensajes entre compradores y vendedores."""

    __tablename__ = "marketplace_messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("marketplace_conversations.id"), nullable=False
    )
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

    # Alias compatibilidad
    @property
    def timestamp(self):
        return self.created_at

    def __repr__(self) -> str:
        return f"<MarketplaceMessage {self.id}>"
