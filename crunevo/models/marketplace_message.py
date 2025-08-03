from datetime import datetime
from crunevo.extensions import db


class MarketplaceMessage(db.Model):
    """Modelo para mensajes entre compradores y vendedores."""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
    product = db.relationship("Product")
    
    def __repr__(self):
        return f"<MarketplaceMessage {self.id}>"


class MarketplaceConversation(db.Model):
    """Modelo para agrupar conversaciones entre usuarios."""
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"))
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    user1 = db.relationship("User", foreign_keys=[user1_id])
    user2 = db.relationship("User", foreign_keys=[user2_id])
    product = db.relationship("Product")
    messages = db.relationship("MarketplaceMessage", 
                              primaryjoin="or_(and_(MarketplaceMessage.sender_id==MarketplaceConversation.user1_id, "
                                         "MarketplaceMessage.receiver_id==MarketplaceConversation.user2_id), "
                                         "and_(MarketplaceMessage.sender_id==MarketplaceConversation.user2_id, "
                                         "MarketplaceMessage.receiver_id==MarketplaceConversation.user1_id))",
                              order_by="MarketplaceMessage.created_at",
                              viewonly=True)
    
    def __repr__(self):
        return f"<MarketplaceConversation {self.id}>"