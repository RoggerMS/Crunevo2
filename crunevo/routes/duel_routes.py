
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.duel import AcademicDuel
from crunevo.models.user import User
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons

duel_bp = Blueprint("duel", __name__)


@duel_bp.route("/retos")
def list_duels():
    recent_duels = AcademicDuel.query.filter(
        AcademicDuel.status.in_(["answered", "validated"])
    ).order_by(AcademicDuel.created_at.desc()).limit(20).all()
    
    pending_duels = []
    my_duels = []
    if current_user.is_authenticated:
        pending_duels = AcademicDuel.query.filter_by(
            challenged_id=current_user.id,
            status="pending"
        ).order_by(AcademicDuel.created_at.desc()).all()
        
        my_duels = AcademicDuel.query.filter(
            db.or_(
                AcademicDuel.challenger_id == current_user.id,
                AcademicDuel.challenged_id == current_user.id
            )
        ).order_by(AcademicDuel.created_at.desc()).limit(10).all()
    
    return render_template(
        "duel/list.html",
        recent_duels=recent_duels,
        pending_duels=pending_duels,
        my_duels=my_duels
    )


@duel_bp.route("/crear-reto", methods=["GET", "POST"])
@login_required
def create_duel():
    if request.method == "POST":
        challenged_username = request.form.get("challenged_username", "").strip()
        question = request.form.get("question", "").strip()
        category = request.form.get("category", "").strip()
        reward = int(request.form.get("reward", 0))
        
        if not all([challenged_username, question, category]):
            flash("Todos los campos son obligatorios", "error")
            return redirect(url_for("duel.create_duel"))
        
        # Find challenged user
        challenged_user = User.query.filter_by(username=challenged_username).first()
        if not challenged_user:
            flash("Usuario no encontrado", "error")
            return redirect(url_for("duel.create_duel"))
        
        if challenged_user.id == current_user.id:
            flash("No puedes retarte a ti mismo", "error")
            return redirect(url_for("duel.create_duel"))
        
        # Check if user has enough credits
        if reward > 0 and current_user.credits < reward:
            flash("No tienes suficientes Crolars para esta recompensa", "error")
            return redirect(url_for("duel.create_duel"))
        
        # Create duel
        duel = AcademicDuel(
            challenger_id=current_user.id,
            challenged_id=challenged_user.id,
            question=question,
            category=category,
            reward_crolars=reward
        )
        db.session.add(duel)
        
        # Deduct reward from challenger if any
        if reward > 0:
            current_user.credits -= reward
        
        db.session.commit()
        
        flash(f"¡Reto enviado a {challenged_user.username}!", "success")
        return redirect(url_for("duel.list_duels"))
    
    categories = [
        "Matemáticas", "Física", "Química", "Biología", "Historia",
        "Literatura", "Inglés", "Programación", "Filosofía", "Economía"
    ]
    
    return render_template("duel/create.html", categories=categories)


@duel_bp.route("/reto/<int:duel_id>/responder", methods=["POST"])
@login_required
def answer_duel(duel_id):
    duel = AcademicDuel.query.get_or_404(duel_id)
    answer = request.form.get("answer", "").strip()
    
    if duel.challenged_id != current_user.id:
        return jsonify({"error": "No tienes permiso para responder este reto"}), 403
    
    if duel.status != "pending":
        return jsonify({"error": "Este reto ya fue respondido"}), 400
    
    if not answer:
        return jsonify({"error": "Debes escribir una respuesta"}), 400
    
    # Update duel
    duel.answer = answer
    duel.status = "answered"
    duel.answered_at = datetime.utcnow()
    
    db.session.commit()
    
    flash("¡Respuesta enviada! Esperando validación del retador.", "success")
    return jsonify({"success": True})


@duel_bp.route("/reto/<int:duel_id>/validar", methods=["POST"])
@login_required
def validate_duel(duel_id):
    duel = AcademicDuel.query.get_or_404(duel_id)
    is_correct = request.form.get("is_correct") == "true"
    
    if duel.challenger_id != current_user.id:
        return jsonify({"error": "Solo el retador puede validar la respuesta"}), 403
    
    if duel.status != "answered":
        return jsonify({"error": "Este reto no ha sido respondido aún"}), 400
    
    # Update duel
    duel.is_correct = is_correct
    duel.status = "validated"
    duel.validated_at = datetime.utcnow()
    
    # Award credits if correct
    if is_correct and duel.reward_crolars > 0:
        add_credit(
            duel.challenged,
            duel.reward_crolars,
            CreditReasons.ACTIVIDAD_SOCIAL,
            related_id=duel_id
        )
    elif not is_correct and duel.reward_crolars > 0:
        # Return credits to challenger
        current_user.credits += duel.reward_crolars
    
    db.session.commit()
    
    result = "correcta" if is_correct else "incorrecta"
    flash(f"Respuesta marcada como {result}", "success")
    return jsonify({"success": True})
