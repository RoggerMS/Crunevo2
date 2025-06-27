from crunevo.models import UserAchievement, Achievement, Credit, AchievementPopup
from crunevo.constants.credit_reasons import CreditReasons
from crunevo.extensions import db
from crunevo.utils.feed import create_feed_item_for_all


def unlock_achievement(user, badge_code):
    """Assign an achievement to the user if not already earned."""
    exists = UserAchievement.query.filter_by(
        user_id=user.id, badge_code=badge_code
    ).first()
    if exists:
        return

    achievement = Achievement.query.filter_by(code=badge_code).first()
    new = UserAchievement(
        user_id=user.id,
        badge_code=badge_code,
        achievement_id=achievement.id if achievement else None,
    )
    db.session.add(new)
    if achievement:
        credit = Credit(
            user_id=user.id,
            amount=achievement.credit_reward or 1,
            reason=CreditReasons.LOGRO,
            related_id=achievement.id,
        )
        db.session.add(credit)
        popup = AchievementPopup(
            user_id=user.id,
            achievement_id=achievement.id,
        )
        db.session.add(popup)
    db.session.commit()
    meta_dict = {
        "badge_code": badge_code,
        "username": user.username,
    }
    create_feed_item_for_all("logro", new.id, meta_dict=meta_dict, is_highlight=True)
