from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from crunevo.extensions import db
from crunevo.models.poll import Poll, PollOption, PollVote
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons

poll_bp = Blueprint("poll", __name__)


@poll_bp.route("/encuestas")
def list_polls():
    active_polls = (
        Poll.query.filter(
            Poll.is_active,
            Poll.expires_at > datetime.utcnow(),
        )
        .order_by(Poll.created_at.desc())
        .all()
    )

    closed_polls = (
        Poll.query.filter(db.or_(~Poll.is_active, Poll.expires_at <= datetime.utcnow()))
        .order_by(Poll.created_at.desc())
        .limit(10)
        .all()
    )

    user_votes = []
    if current_user.is_authenticated:
        user_votes = [
            v.poll_id for v in PollVote.query.filter_by(user_id=current_user.id).all()
        ]

    return render_template(
        "poll/list.html",
        active_polls=active_polls,
        closed_polls=closed_polls,
        user_votes=user_votes,
    )


@poll_bp.route("/crear-encuesta", methods=["GET", "POST"])
@login_required
def create_poll():
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        options = [
            opt.strip() for opt in request.form.getlist("options") if opt.strip()
        ]
        duration_hours = int(request.form.get("duration", 24))

        if not question or len(question) > 120:
            flash("La pregunta debe tener entre 1 y 120 caracteres", "error")
            return redirect(url_for("poll.create_poll"))

        if len(options) < 2 or len(options) > 4:
            flash("Debes agregar entre 2 y 4 opciones", "error")
            return redirect(url_for("poll.create_poll"))

        # Create poll
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        poll = Poll(question=question, author_id=current_user.id, expires_at=expires_at)
        db.session.add(poll)
        db.session.flush()

        # Create options
        for option_text in options:
            option = PollOption(poll_id=poll.id, text=option_text)
            db.session.add(option)

        db.session.commit()

        # Award credits
        add_credit(current_user, 2, CreditReasons.ACTIVIDAD_SOCIAL, related_id=poll.id)

        flash("¡Encuesta creada exitosamente!", "success")
        return redirect(url_for("poll.list_polls"))

    return render_template("poll/create.html")


@poll_bp.route("/encuesta/<int:poll_id>/votar", methods=["POST"])
@login_required
def vote_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    option_id = request.form.get("option_id")

    if not option_id:
        return jsonify({"error": "Debes seleccionar una opción"}), 400

    # Check if already voted
    existing_vote = PollVote.query.filter_by(
        user_id=current_user.id, poll_id=poll_id
    ).first()
    if existing_vote:
        return jsonify({"error": "Ya has votado en esta encuesta"}), 400

    # Check if poll is active
    if not poll.is_active or poll.is_expired:
        return jsonify({"error": "Esta encuesta ya no está activa"}), 400

    # Create vote
    vote = PollVote(poll_id=poll_id, option_id=option_id, user_id=current_user.id)
    db.session.add(vote)

    # Update counters
    option = PollOption.query.get(option_id)
    option.vote_count += 1
    poll.total_votes += 1

    db.session.commit()

    # Award credits
    add_credit(current_user, 1, CreditReasons.ACTIVIDAD_SOCIAL, related_id=poll_id)

    return jsonify({"success": True, "results": poll.get_results()})
