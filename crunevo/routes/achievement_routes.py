from flask import Blueprint
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models import AchievementPopup

ach_bp = Blueprint("achievement_popup", __name__)


@ach_bp.route("/api/achievement-popup/mark-shown", methods=["POST"])
@login_required
def mark_achievement_popup_seen():
    AchievementPopup.query.filter_by(user_id=current_user.id, shown=False).update(
        {"shown": True}
    )
    db.session.commit()
    return "", 204
