from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.hall_1000 import (
    CrolarsHallMember,
    PremiumContent,
    HallRaffle,
    RaffleParticipant,
)
from crunevo.models.purchase import Purchase
from crunevo.utils.helpers import activated_required
from datetime import datetime

hall_bp = Blueprint("hall", __name__, url_prefix="/sala-1000")


@hall_bp.route("/")
@login_required
@activated_required
def index():
    """1000 Crolars Hall main page"""
    # Check if user has access
    member = CrolarsHallMember.query.filter_by(user_id=current_user.id).first()

    if not member:
        # Calculate total spent
        total_spent = (
            db.session.query(db.func.sum(Purchase.total_price))
            .filter(Purchase.user_id == current_user.id, Purchase.status == "completed")
            .scalar()
            or 0
        )

        if total_spent < 1000:
            return render_template(
                "hall/locked.html", total_spent=total_spent, needed=1000 - total_spent
            )
        else:
            # Unlock access
            member = unlock_hall_access(current_user.id, total_spent)

    # Get premium content
    premium_content = (
        PremiumContent.query.filter(
            PremiumContent.is_active.is_(True),
            PremiumContent.required_level <= get_access_level(member.total_spent),
        )
        .order_by(PremiumContent.created_at.desc())
        .all()
    )

    # Get active raffles
    active_raffles = HallRaffle.query.filter(
        HallRaffle.is_active.is_(True),
        HallRaffle.end_date > datetime.utcnow(),
    ).all()

    # Get hall statistics
    total_members = CrolarsHallMember.query.count()
    total_content = PremiumContent.query.filter_by(is_active=True).count()

    return render_template(
        "hall/index.html",
        member=member,
        premium_content=premium_content,
        active_raffles=active_raffles,
        total_members=total_members,
        total_content=total_content,
    )


@hall_bp.route("/contenido-premium")
@login_required
@activated_required
def premium_content():
    """Premium content library"""
    member = check_hall_access()
    if not member:
        return redirect(url_for("hall.index"))

    content_type = request.args.get("type", "all")

    query = PremiumContent.query.filter_by(is_active=True)

    if content_type != "all":
        query = query.filter_by(content_type=content_type)

    # Filter by access level
    user_level = get_access_level_rank(member.access_level)
    query = query.filter(PremiumContent.required_level <= user_level)

    content = query.order_by(PremiumContent.created_at.desc()).all()

    return render_template(
        "hall/premium_content.html",
        member=member,
        content=content,
        content_type=content_type,
    )


@hall_bp.route("/descargar/<int:content_id>")
@login_required
@activated_required
def download_content(content_id):
    """Download premium content"""
    member = check_hall_access()
    if not member:
        return jsonify({"error": "Acceso denegado"}), 403

    content = PremiumContent.query.get_or_404(content_id)

    # Check access level
    user_level = get_access_level_rank(member.access_level)
    required_level = get_access_level_rank(content.required_level)

    if user_level < required_level:
        return jsonify({"error": "Nivel de acceso insuficiente"}), 403

    # Update download count
    content.download_count += 1
    member.premium_downloads += 1

    db.session.commit()

    # Return file URL (implement actual file serving logic)
    return jsonify(
        {
            "success": True,
            "download_url": content.file_url,
            "filename": f"{content.title}.pdf",
        }
    )


@hall_bp.route("/sorteos")
@login_required
@activated_required
def raffles():
    """Hall raffles page"""
    member = check_hall_access()
    if not member:
        return redirect(url_for("hall.index"))

    # Get active raffles
    active_raffles = HallRaffle.query.filter(
        HallRaffle.is_active.is_(True),
        HallRaffle.end_date > datetime.utcnow(),
    ).all()

    # Get user's participations
    user_participations = {}
    for raffle in active_raffles:
        participation = RaffleParticipant.query.filter_by(
            raffle_id=raffle.id, user_id=current_user.id
        ).first()
        user_participations[raffle.id] = participation

    # Get completed raffles
    completed_raffles = (
        HallRaffle.query.filter(HallRaffle.is_completed.is_(True))
        .order_by(HallRaffle.end_date.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "hall/raffles.html",
        member=member,
        active_raffles=active_raffles,
        completed_raffles=completed_raffles,
        user_participations=user_participations,
    )


@hall_bp.route("/participar-sorteo/<int:raffle_id>", methods=["POST"])
@login_required
@activated_required
def join_raffle(raffle_id):
    """Join a raffle"""
    member = check_hall_access()
    if not member:
        return jsonify({"error": "Acceso denegado"}), 403

    raffle = HallRaffle.query.get_or_404(raffle_id)

    # Check if raffle is active
    if not raffle.is_active or raffle.end_date <= datetime.utcnow():
        return jsonify({"error": "Sorteo no disponible"}), 400

    # Check if user already participated
    existing_participation = RaffleParticipant.query.filter_by(
        raffle_id=raffle_id, user_id=current_user.id
    ).first()

    if existing_participation:
        return jsonify({"error": "Ya participas en este sorteo"}), 400

    # Check if user has enough raffle entries
    if member.raffle_entries < raffle.entry_cost:
        return jsonify({"error": "No tienes suficientes entradas de sorteo"}), 400

    # Check max participants
    current_participants = raffle.participants.count()
    if current_participants >= raffle.max_participants:
        return jsonify({"error": "Sorteo completo"}), 400

    # Create participation
    participation = RaffleParticipant(
        raffle_id=raffle_id, user_id=current_user.id, entries_used=raffle.entry_cost
    )

    # Deduct raffle entries
    member.raffle_entries -= raffle.entry_cost

    db.session.add(participation)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": f"¡Te has unido al sorteo! Entradas restantes: {member.raffle_entries}",
        }
    )


@hall_bp.route("/mi-progreso")
@login_required
@activated_required
def my_progress():
    """User's hall progress page"""
    member = check_hall_access()
    if not member:
        return redirect(url_for("hall.index"))

    # Get spending history
    purchases = (
        Purchase.query.filter(
            Purchase.user_id == current_user.id, Purchase.status == "completed"
        )
        .order_by(Purchase.created_at.desc())
        .limit(20)
        .all()
    )

    # Calculate next level requirements
    next_level_spent = get_next_level_requirement(member.access_level)

    return render_template(
        "hall/my_progress.html",
        member=member,
        purchases=purchases,
        next_level_spent=next_level_spent,
    )


def check_hall_access():
    """Check if user has hall access"""
    return CrolarsHallMember.query.filter_by(user_id=current_user.id).first()


def unlock_hall_access(user_id, total_spent):
    """Unlock hall access for user"""
    access_level = get_access_level(total_spent)

    member = CrolarsHallMember(
        user_id=user_id,
        total_spent=total_spent,
        access_level=access_level,
        raffle_entries=calculate_initial_entries(total_spent),
    )

    db.session.add(member)
    db.session.commit()

    return member


def get_access_level(total_spent):
    """Determine access level based on total spent"""
    if total_spent >= 5000:
        return "platinum"
    elif total_spent >= 3000:
        return "gold"
    elif total_spent >= 2000:
        return "silver"
    else:
        return "bronze"


def get_access_level_rank(level):
    """Get numeric rank for access level"""
    levels = {"bronze": 1, "silver": 2, "gold": 3, "platinum": 4}
    return levels.get(level, 1)


def get_next_level_requirement(current_level):
    """Get Crolars requirement for next level"""
    requirements = {"bronze": 2000, "silver": 3000, "gold": 5000, "platinum": None}
    return requirements.get(current_level)


def calculate_initial_entries(total_spent):
    """Calculate initial raffle entries based on spending"""
    return min(10, total_spent // 500)  # 1 entry per 500 Crolars spent, max 10


def update_hall_member_spending(user_id, amount):
    """Update hall member spending when purchase is made"""
    member = CrolarsHallMember.query.filter_by(user_id=user_id).first()

    if member:
        member.total_spent += amount
        new_level = get_access_level(member.total_spent)

        if new_level != member.access_level:
            member.access_level = new_level
            # Award bonus raffle entries for level up
            member.raffle_entries += 5

        # Award raffle entry for every 100 Crolars spent
        if amount >= 100:
            member.raffle_entries += amount // 100

        db.session.commit()
