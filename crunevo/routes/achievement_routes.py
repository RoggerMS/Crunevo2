from flask import Blueprint, session, jsonify
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models import AchievementPopup

ach_bp = Blueprint("achievement_popup", __name__)


@ach_bp.before_app_request
def clear_session_new_achievements():
    if current_user.is_authenticated:
        print(
            "\U0001F525 Revisando sesi\u00f3n de logros…",
            session.get("new_achievements"),
        )
        has_pending = AchievementPopup.query.filter_by(
            user_id=current_user.id, shown=False
        ).count()
        if not has_pending:
            session.pop("new_achievements", None)


@ach_bp.route("/api/achievement-popup/mark-shown", methods=["POST"])
@login_required
def mark_achievement_popup_seen():
    print("\U0001F9E0 Marcar logros como vistos para:", current_user.username)
    AchievementPopup.query.filter_by(user_id=current_user.id, shown=False).update(
        {"shown": True}
    )
    db.session.commit()
    session["new_achievements"] = []
    return jsonify({"success": True})
