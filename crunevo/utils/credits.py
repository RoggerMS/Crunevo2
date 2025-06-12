from crunevo.models import Credit
from crunevo.extensions import db


def add_credit(user, amount, reason, related_id=None):
    """Register a credit transaction and update user balance."""
    credit = Credit(user_id=user.id, amount=amount, reason=reason, related_id=related_id)
    user.credits += amount
    db.session.add(credit)
    db.session.commit()
