from crunevo.models import UserAchievement
from crunevo.extensions import db
from crunevo.utils.feed import create_feed_item_for_all


def unlock_achievement(user, badge_code):
    """Assign an achievement to the user if not already earned."""
    exists = UserAchievement.query.filter_by(
        user_id=user.id, badge_code=badge_code
    ).first()
    if exists:
        return

    new = UserAchievement(user_id=user.id, badge_code=badge_code)
    db.session.add(new)
    db.session.commit()
    meta_dict = {
        "badge_code": badge_code,
        "username": user.username,
    }
    create_feed_item_for_all("logro", new.id, meta_dict=meta_dict, is_highlight=True)
