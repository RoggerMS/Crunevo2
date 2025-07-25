from datetime import datetime, timedelta
from flask import Blueprint, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy import func
from crunevo.models import (
    Mission,
    UserMission,
    GroupMission,
    GroupMissionParticipant,
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


def progress_for_code(user, code, category=None):
    """Calculate progress for a mission code."""
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    progress = 0

    if code.startswith("subir_apuntes_") or code == "primer_apunte":
        progress = Note.query.filter_by(user_id=user.id).count()
        if category == "diaria":
            progress = (
                Note.query.filter_by(user_id=user.id)
                .filter(Note.created_at >= one_day_ago)
                .count()
            )
    elif code.startswith("comentar_"):
        progress = (
            PostComment.query.filter_by(author_id=user.id)
            .filter(PostComment.timestamp >= one_day_ago)
            .count()
        )
    elif code.startswith("likes_") or code == "primer_like":
        progress = (
            db.session.query(func.coalesce(func.sum(Post.likes), 0))
            .filter_by(author_id=user.id)
            .scalar()
            or 0
        )
    elif code.startswith("comprar_producto_"):
        progress = Purchase.query.filter_by(user_id=user.id).count()
    elif code.startswith("referido_"):
        try:
            completed_refs = Referral.query.filter_by(
                invitador_id=user.id, completado=True
            ).count()
            if code == "referido_maraton":
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
    elif code == "maraton_apuntes":
        progress = (
            Note.query.filter_by(user_id=user.id)
            .filter(Note.created_at >= one_day_ago)
            .count()
        )

    return progress


def compute_mission_states(user):
    """Return progress information for all missions of a user."""
    now = datetime.utcnow()

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
        progress = progress_for_code(user, m.code, getattr(m, "category", None))

        completed = progress >= m.goal
        record = UserMission.query.filter_by(user_id=user.id, mission_id=m.id).first()

        progress_dict[m.id] = {
            "progreso": progress,
            "completada": completed,
            "reclamada": record is not None,
            "id": record.id if record else None,
        }

    return progress_dict


def compute_group_mission_states(user):
    """Return aggregated progress for group missions of a user."""
    groups = (
        GroupMission.query.join(GroupMissionParticipant)
        .filter(GroupMissionParticipant.user_id == user.id)
        .all()
    )
    result = {}
    for gm in groups:
        # update individual progress records
        for part in gm.participants:
            part.progress = progress_for_code(
                part.user, gm.code, getattr(gm, "category", None)
            )
        total = sum(p.progress for p in gm.participants)
        entry = next((p for p in gm.participants if p.user_id == user.id), None)
        claimed = entry.claimed if entry else False
        completed = total >= gm.goal
        result[gm.id] = {
            "mission": gm,
            "progress": total,
            "completed": completed,
            "claimed": claimed,
        }
    db.session.commit()
    return result


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


@missions_bp.route("/reclamar_mision_grupal/<int:group_id>", methods=["POST"])
@login_required
def reclamar_mision_grupal(group_id):
    """Allow a user to claim a completed group mission."""
    gm = GroupMission.query.get_or_404(group_id)
    participant = GroupMissionParticipant.query.filter_by(
        group_mission_id=group_id, user_id=current_user.id
    ).first()
    if not participant:
        flash("No participas en esta misi\u00f3n", "warning")
        return redirect(url_for("auth.perfil", tab="misiones"))
    if participant.claimed:
        flash("Misi\u00f3n ya reclamada", "info")
        return redirect(url_for("auth.perfil", tab="misiones"))

    total = sum(p.progress for p in gm.participants)
    if total < gm.goal:
        flash("A\u00fan no han completado esta misi\u00f3n", "warning")
        return redirect(url_for("auth.perfil", tab="misiones"))

    participant.claimed = True
    add_credit(current_user, gm.credit_reward, CreditReasons.DONACION)
    db.session.commit()
    flash("\u00a1Cr\u00e9ditos reclamados!", "success")
    return redirect(url_for("auth.perfil", tab="misiones"))


@missions_bp.route("/")
def list_missions():
    """Legacy route; redirect to profile missions tab."""
    return redirect(url_for("auth.perfil", tab="misiones"))
