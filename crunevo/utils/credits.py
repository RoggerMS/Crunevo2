from crunevo.models import Credit
from crunevo.extensions import db
from crunevo.constants import AchievementCodes, CreditReasons
from crunevo.utils.achievements import unlock_achievement
from crunevo.utils.feed import create_feed_item_for_all
from flask_login import current_user
from flask import has_request_context


def add_credit(user, amount, reason, related_id=None):
    """Register a credit transaction and update user balance."""
    credit = Credit(
        user_id=user.id, amount=amount, reason=reason, related_id=related_id
    )
    user.credits += amount
    db.session.add(credit)
    db.session.commit()
    if user.credits >= 100:
        unlock_achievement(user, AchievementCodes.CREDITOS_100)
    if (
        amount > 0
        and has_request_context()
        and current_user.is_authenticated
        and current_user.id != user.id
    ):
        meta = {
            "amount": amount,
            "reason": reason,
            "sender": current_user.username,
            "receiver": user.username,
        }
        create_feed_item_for_all(
            "movimiento",
            credit.id,
            meta_dict=meta,
            owner_ids=[current_user.id, user.id],
            is_highlight=True,
        )


def spend_credit(user, amount, reason, related_id=None):
    """Spend credits if the user has enough, recording the transaction."""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if user.credits < amount:
        raise ValueError("Crolars insuficientes")
    credit = Credit(
        user_id=user.id, amount=-amount, reason=reason, related_id=related_id
    )
    user.credits -= amount
    db.session.add(credit)
    db.session.commit()
    if (
        amount > 0
        and has_request_context()
        and current_user.is_authenticated
        and current_user.id != user.id
    ):
        meta = {
            "amount": amount,
            "reason": reason,
            "sender": user.username,
            "receiver": current_user.username,
        }
        create_feed_item_for_all(
            "movimiento",
            credit.id,
            meta_dict=meta,
            owner_ids=[user.id, current_user.id],
            is_highlight=True,
        )

    voluntary_reasons = {
        CreditReasons.DONACION,
        CreditReasons.DONACION_FEED,
        CreditReasons.AGRADECIMIENTO,
        "donacion",
        "agradecimiento",
        "donación",
    }
    if isinstance(reason, str) and reason.lower() in voluntary_reasons:
        unlock_achievement(user, AchievementCodes.DONADOR)
