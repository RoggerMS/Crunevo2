from flask import Blueprint, session, jsonify, current_app
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models import AchievementPopup


# Define the blueprint and keep a short alias for backwards compatibility.
achievement_bp = Blueprint("achievement_popup", __name__)
ach_bp = achievement_bp


@ach_bp.before_app_request
def clear_session_new_achievements():
    try:
        if current_user.is_authenticated:
            current_value = session.get("new_achievements")
            if current_value:
                current_app.logger.debug("🔥 Revisando sesión de logros… %s", current_value)
            has_pending = AchievementPopup.query.filter_by(
                user_id=current_user.id, shown=False
            ).count()
            if not has_pending:
                session.pop("new_achievements", None)
    except Exception as e:
        # Silently handle any errors during app initialization
        pass


@ach_bp.route("/api/achievement-popup/mark-shown", methods=["POST"])
@login_required
def mark_shown():
    try:
        current_app.logger.debug(
            "🧠 Marcar logros como vistos para: %s", current_user.username
        )
        q = AchievementPopup.query.filter_by(user_id=current_user.id, shown=False)
        if q.count() == 0:
            return jsonify({"success": True, "message": "No hay logros pendientes"})
        q.update({"shown": True}, synchronize_session=False)
        db.session.commit()
        session.pop("new_achievements", None)
        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.warning("⚠️ Error al marcar logros como vistos: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
