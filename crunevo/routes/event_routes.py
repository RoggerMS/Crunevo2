from flask import (
    Blueprint,
    render_template,
    flash,
    jsonify,
    url_for,
    request,
    redirect,
)
from datetime import datetime
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.event import Event
from crunevo.models.event_participation import EventParticipation
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons
from crunevo.utils.helpers import admin_required
import json

event_bp = Blueprint("event", __name__)


@event_bp.route("/eventos")
def list_events():
    from sqlalchemy import func

    upcoming_events = (
        Event.query.filter(Event.event_date > func.now())
        .order_by(Event.event_date.asc())
        .all()
    )
    past_events = (
        Event.query.filter(Event.event_date <= func.now())
        .order_by(Event.event_date.desc())
        .limit(5)
        .all()
    )

    user_participations = []
    if current_user.is_authenticated:
        user_participations = [
            p.event_id
            for p in EventParticipation.query.filter_by(user_id=current_user.id).all()
        ]

    return render_template(
        "event/list.html",
        upcoming_events=upcoming_events,
        past_events=past_events,
        user_participations=user_participations,
    )


@event_bp.route("/evento/<int:event_id>")
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    is_participating = False
    participant_count = EventParticipation.query.filter_by(event_id=event_id).count()

    if current_user.is_authenticated:
        is_participating = (
            EventParticipation.query.filter_by(
                user_id=current_user.id, event_id=event_id
            ).first()
            is not None
        )

    recent_participants = (
        EventParticipation.query.filter_by(event_id=event_id)
        .order_by(EventParticipation.joined_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "event/detail.html",
        event=event,
        is_participating=is_participating,
        participant_count=participant_count,
        recent_participants=recent_participants,
    )


@event_bp.route("/evento/<int:event_id>/participar", methods=["POST"])
@login_required
def join_event(event_id):
    event = Event.query.get_or_404(event_id)

    # Check if already participating
    existing = EventParticipation.query.filter_by(
        user_id=current_user.id, event_id=event_id
    ).first()

    if existing:
        return jsonify({"error": "Ya estás participando en este evento"}), 400

    # Check if event is still upcoming
    if event.event_date <= datetime.utcnow():
        return jsonify({"error": "Este evento ya ha terminado"}), 400

    # Join event
    participation = EventParticipation(user_id=current_user.id, event_id=event_id)

    db.session.add(participation)
    db.session.commit()

    # Award credits
    add_credit(current_user, 3, CreditReasons.ACTIVIDAD_SOCIAL, related_id=event_id)

    flash(f"¡Te has unido al evento {event.title}!")
    return jsonify({"success": True})


@event_bp.route("/evento/<int:event_id>/abandonar", methods=["POST"])
@login_required
def leave_event(event_id):
    event = Event.query.get_or_404(event_id)
    participation = EventParticipation.query.filter_by(
        user_id=current_user.id, event_id=event_id
    ).first()

    if not participation:
        return jsonify({"error": "No estás participando en este evento"}), 400

    db.session.delete(participation)
    db.session.commit()

    flash(f"Has abandonado el evento {event.title}")
    return jsonify({"success": True})


@event_bp.route("/eventos/calendario")
def events_calendar():
    events = Event.query.all()
    data = [
        {
            "id": e.id,
            "title": e.title,
            "start": e.event_date.isoformat(),
            "notification_times": e.notification_times,
            "recurring": e.recurring,
            "url": url_for("event.view_event", event_id=e.id),
        }
        for e in events
    ]
    return jsonify(data)


@event_bp.route("/admin/eventos")
@login_required
@admin_required
def admin_list_events():
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template("admin/events.html", events=events)


@event_bp.route("/admin/evento/crear", methods=["GET", "POST"])
@login_required
@admin_required
def admin_create_event():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        event_date = request.form.get("event_date")
        category = request.form.get("category", "").strip()
        image_url = request.form.get("image_url", "").strip()
        jitsi_url = request.form.get("jitsi_url", "").strip()
        zoom_url = request.form.get("zoom_url", "").strip()
        is_featured = request.form.get("is_featured") == "on"
        rewards = request.form.get("rewards", "").strip()

        if not all([title, event_date]):
            flash("Título y fecha son obligatorios", "error")
            return redirect(url_for("event.admin_create_event"))

        try:
            event_datetime = datetime.strptime(event_date, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Formato de fecha inválido", "error")
            return redirect(url_for("event.admin_create_event"))

        event = Event(
            title=title,
            description=description,
            event_date=event_datetime,
            category=category,
            image_url=image_url or None,
            jitsi_url=jitsi_url or None,
            zoom_url=zoom_url or None,
            is_featured=is_featured,
            rewards=rewards or None,
        )

        db.session.add(event)
        db.session.commit()

        flash("Evento creado exitosamente", "success")
        return redirect(url_for("event.admin_list_events"))

    return render_template("admin/admin_event_form.html", event=None, action="crear")


@event_bp.route("/admin/evento/<int:event_id>/participantes")
@login_required
def admin_event_participants(event_id):
    if current_user.role not in ["admin", "moderator"]:
        flash("No tienes permisos para acceder a esta sección", "error")
        return redirect(url_for("event.list_events"))

    event = Event.query.get_or_404(event_id)
    participants = EventParticipation.query.filter_by(event_id=event_id).all()

    return render_template(
        "admin/event_participants.html", event=event, participants=participants
    )
