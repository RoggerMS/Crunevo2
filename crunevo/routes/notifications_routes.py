from flask import Blueprint, render_template
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from crunevo.models import Notification

noti_bp = Blueprint("noti", __name__)


@noti_bp.route("/notificaciones")
@activated_required
def ver_notificaciones():
    notificaciones = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.timestamp.desc())
        .all()
    )
    return render_template("notificaciones/lista.html", notificaciones=notificaciones)
