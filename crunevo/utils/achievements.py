from crunevo.models import UserAchievement
from crunevo.extensions import db
from crunevo.utils.feed import create_feed_item_for_all


def unlock_achievement(user, badge_code):
    if not any(a.badge_code == badge_code for a in user.achievements):
        new = UserAchievement(user_id=user.id, badge_code=badge_code)
        db.session.add(new)
        db.session.commit()
        meta_dict = {
            'badge_code': badge_code,
            'username': user.username,
        }
        create_feed_item_for_all('logro', new.id, meta_dict=meta_dict, is_highlight=True)

