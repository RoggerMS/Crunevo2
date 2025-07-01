from flask import Blueprint, render_template, jsonify, abort
from flask_login import current_user, login_required
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Notification

noti_bp = Blueprint("noti", __name__)


@noti_bp.route("/notificaciones")
@noti_bp.route("/notifications")
@activated_required
def ver_notificaciones():
    notificaciones = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.timestamp.desc())
        .all()
    )
    return render_template("notificaciones/lista.html", notificaciones=notificaciones)


@noti_bp.route("/notifications/read_all", methods=["POST"])
@login_required
def marcar_leidas():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return jsonify({"status": "ok"})


@noti_bp.route("/notifications/delete/<int:noti_id>", methods=["POST"])
@login_required
def borrar_noti(noti_id):
    n = Notification.query.get_or_404(noti_id)
    if n.user_id != current_user.id:
        abort(403)
    db.session.delete(n)
    db.session.commit()
    return jsonify({"status": "ok"})


@noti_bp.route("/api/notifications")
@login_required
def api_notifications():
    unread = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.timestamp.desc())
        .limit(5)
        .all()
    )
    return jsonify(
        [
            {
                "id": n.id,
                "message": n.message,
                "url": n.url,
                "timestamp": n.timestamp.isoformat(),
            }
            for n in unread
        ]
    )


@noti_bp.route("/notifications/api/count")
@login_required
def api_notifications_count():
    """Return the number of unread notifications for the current user."""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({"count": count})
