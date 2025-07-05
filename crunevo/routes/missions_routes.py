from datetime import datetime, timedelta
from flask import Blueprint, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy import func
from crunevo.models import (
    Mission,
    UserMission,
    Note,
    PostComment,
    Post,
    Purchase,
    Referral,
    DeviceClaim,
    Event,
)
from crunevo.extensions import db
from crunevo.utils.credits import add_credit
from crunevo.constants import CreditReasons

missions_bp = Blueprint("missions", __name__, url_prefix="/misiones")


def compute_mission_states(user):
    """Return progress information for all missions of a user."""
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)

    missions = Mission.query.all()
    progress_dict = {}
    upcoming_window = now + timedelta(days=7)
    changes = False

    for m in missions:
        if m.event_id:
            event = Event.query.get(m.event_id)
            should_activate = False
            if event:
                should_activate = (
                    event.event_date <= upcoming_window and event.event_date > now
                )
            if m.is_active != should_activate:
                m.is_active = should_activate
                changes = True

    if changes:
        db.session.commit()

    for m in missions:
        if m.event_id and not m.is_active:
            progress_dict[m.id] = {
                "progreso": 0,
                "completada": False,
                "reclamada": False,
                "id": None,
            }
            continue
        progress = 0

        # 📝 Subir apuntes
        if m.code.startswith("subir_apuntes_") or m.code == "primer_apunte":
            progress = Note.query.filter_by(user_id=user.id).count()
            if getattr(m, "category", None) == "diaria":
                progress = (
                    Note.query.filter_by(user_id=user.id)
                    .filter(Note.created_at >= one_day_ago)
                    .count()
                )

        # 💬 Comentar publicaciones
        elif m.code.startswith("comentar_"):
            progress = (
                PostComment.query.filter_by(author_id=user.id)
                .filter(PostComment.timestamp >= one_day_ago)
                .count()
            )

        # 👍 Recibir likes
        elif m.code.startswith("likes_") or m.code == "primer_like":
            progress = (
                db.session.query(func.coalesce(func.sum(Post.likes), 0))
                .filter_by(author_id=user.id)
                .scalar()
                or 0
            )

        # 🛒 Compras en tienda
        elif m.code.startswith("comprar_producto_"):
            progress = Purchase.query.filter_by(user_id=user.id).count()

        # 👥 Referidos activos
        elif m.code.startswith("referido_"):
            try:
                completed_refs = Referral.query.filter_by(
                    invitador_id=user.id, completado=True
                ).count()
                if m.code == "referido_maraton":
                    week_ago = datetime.utcnow() - timedelta(days=7)
                    progress = (
                        Referral.query.filter_by(invitador_id=user.id, completado=True)
                        .filter(Referral.fecha_creacion >= week_ago)
                        .count()
                    )
                else:
                    progress = completed_refs
            except Exception:
                db.session.rollback()
                progress = 0

        # 🏆 Logros únicos
        elif m.code == "maraton_apuntes":
            progress = (
                Note.query.filter_by(user_id=user.id)
                .filter(Note.created_at >= one_day_ago)
                .count()
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
        flash("Misi\u00f3n ya reclamada", "info")
        return redirect(url_for("auth.perfil", tab="misiones"))

    token = request.headers.get("X-Device-Token")
    if token:
        limit = datetime.utcnow() - timedelta(hours=24)
        exists = (
            DeviceClaim.query.filter_by(device_token=token, mission_code=mission.code)
            .filter(DeviceClaim.timestamp >= limit)
            .first()
        )
        if exists:
            message = "Este dispositivo ya canjeó esta recompensa recientemente."
            flash(message, "warning")
            resp = redirect(url_for("auth.perfil", tab="misiones"))
            resp.set_data(message)
            return resp

    progress = compute_mission_states(current_user).get(mission_id)
    if not progress or not progress["completada"]:
        flash("A\u00fan no has completado esta misi\u00f3n", "warning")
        return redirect(url_for("auth.perfil", tab="misiones"))

    db.session.add(UserMission(user_id=current_user.id, mission_id=mission_id))
    add_credit(current_user, mission.credit_reward, CreditReasons.DONACION)
    if token:
        db.session.add(
            DeviceClaim(
                device_token=token,
                mission_code=mission.code,
                user_id=current_user.id,
            )
        )
    db.session.commit()
    flash("\u00a1Cr\u00e9ditos reclamados!", "success")
    return redirect(url_for("auth.perfil", tab="misiones"))


@missions_bp.route("/")
def list_missions():
    """Legacy route; redirect to profile missions tab."""
    return redirect(url_for("auth.perfil", tab="misiones"))
