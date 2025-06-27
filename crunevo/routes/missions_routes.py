from datetime import datetime, timedelta
from flask import Blueprint, redirect, url_for, flash
from flask_login import current_user, login_required
from sqlalchemy import func
from crunevo.models import Mission, UserMission, Note, PostComment, Post
from crunevo.extensions import db
from crunevo.utils.credits import add_credit
from crunevo.constants import CreditReasons

missions_bp = Blueprint("missions", __name__, url_prefix="/misiones")


def compute_mission_states(user):
    """Return mission progress dict for a user without claiming."""
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    # Ensure default missions exist
    defaults = [
        {
            "code": "upload_note",
            "description": "Subir 1 apunte esta semana",
            "goal": 1,
            "credit_reward": 5,
        },
        {
            "code": "comment_posts",
            "description": "Comentar en 3 publicaciones",
            "goal": 3,
            "credit_reward": 3,
        },
        {
            "code": "receive_likes",
            "description": "Recibir 5 likes en tus publicaciones",
            "goal": 5,
            "credit_reward": 3,
        },
    ]
    for d in defaults:
        if not Mission.query.filter_by(code=d["code"]).first():
            db.session.add(Mission(**d))
    db.session.commit()

    missions = Mission.query.all()
    progress_dict = {}
    for m in missions:
        progress = 0
        if m.code == "upload_note":
            progress = (
                Note.query.filter_by(user_id=user.id)
                .filter(Note.created_at >= one_week_ago)
                .count()
            )
        elif m.code == "comment_posts":
            progress = (
                PostComment.query.filter_by(author_id=user.id)
                .filter(PostComment.timestamp >= one_week_ago)
                .count()
            )
        elif m.code == "receive_likes":
            progress = (
                db.session.query(func.coalesce(func.sum(Post.likes), 0))
                .filter_by(author_id=user.id)
                .scalar()
                or 0
            )
        completed = progress >= m.goal
        record = UserMission.query.filter_by(user_id=user.id, mission_id=m.id).first()
        progress_dict[m.id] = {
            "progreso": progress,
            "completada": completed,
            "reclamada": record is not None,
            "id": record.id if record else None,
        }
    return progress_dict


@missions_bp.route("/reclamar_mision/<int:mission_id>", methods=["POST"])
@login_required
def reclamar_mision(mission_id):
    """Allow the current user to claim a completed mission."""
    mission = Mission.query.get_or_404(mission_id)
    record = UserMission.query.filter_by(
        user_id=current_user.id, mission_id=mission_id
    ).first()
    if record:
        flash("Misión ya reclamada", "info")
        return redirect(url_for("auth.perfil", tab="misiones"))

    progress = compute_mission_states(current_user).get(mission_id)
    if not progress or not progress["completada"]:
        flash("Aún no has completado esta misión", "warning")
        return redirect(url_for("auth.perfil", tab="misiones"))

    db.session.add(UserMission(user_id=current_user.id, mission_id=mission_id))
    add_credit(current_user, mission.credit_reward, CreditReasons.DONACION)
    db.session.commit()
    flash("¡Créditos reclamados!", "success")
    return redirect(url_for("auth.perfil", tab="misiones"))


@missions_bp.route("/")
def list_missions():
    """Legacy route; redirect to profile missions tab."""
    return redirect(url_for("auth.perfil", tab="misiones"))
