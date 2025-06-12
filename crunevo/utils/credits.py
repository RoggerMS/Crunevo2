from crunevo.models import Credit
from crunevo.extensions import db


def add_credit(user, amount, reason, related_id=None):
    """Register a credit transaction and update user balance."""
    credit = Credit(user_id=user.id, amount=amount, reason=reason, related_id=related_id)
    user.credits += amount
    db.session.add(credit)
    db.session.commit()


def spend_credit(user, amount, reason, related_id=None):
    """Spend credits if the user has enough, recording the transaction."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if user.credits < amount:
        raise ValueError("Créditos insuficientes")
    credit = Credit(user_id=user.id, amount=-amount, reason=reason, related_id=related_id)
    user.credits -= amount
    db.session.add(credit)
    db.session.commit()
