from crunevo.models import Achievement, UserAchievement
from crunevo.extensions import db
from crunevo.utils.feed import create_feed_item_for_all
from crunevo.constants import ACHIEVEMENT_DETAILS


def unlock_achievement(user, badge_code):
    """Assign an achievement to the user if not already earned."""
    ach = Achievement.query.filter_by(code=badge_code).first()
    if ach is None:
        details = ACHIEVEMENT_DETAILS.get(badge_code, {})
        ach = Achievement(
            code=badge_code,
            title=details.get("title", badge_code.title()),
            icon=details.get("icon", "bi-star"),
        )
        db.session.add(ach)
        db.session.commit()

    exists = UserAchievement.query.filter_by(
        user_id=user.id, achievement_id=ach.id
    ).first()
    if exists:
        return

    new = UserAchievement(user_id=user.id, achievement_id=ach.id)
    db.session.add(new)
    db.session.commit()
    meta_dict = {
        "badge_code": badge_code,
        "username": user.username,
    }
    create_feed_item_for_all("logro", new.id, meta_dict=meta_dict, is_highlight=True)
