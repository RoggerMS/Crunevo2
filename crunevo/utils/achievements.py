from crunevo.models import UserAchievement
from crunevo.extensions import db


def unlock_achievement(user, badge_code):
    if not any(a.badge_code == badge_code for a in user.achievements):
        new = UserAchievement(user_id=user.id, badge_code=badge_code)
        db.session.add(new)
        db.session.commit()

