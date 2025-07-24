from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.challenges import (
    GhostMentorChallenge,
    GhostMentorResponse,
    MasterQuestion,
    MasterQuestionAttempt,
)
from crunevo.utils.helpers import activated_required, table_exists
from crunevo.utils.credits import add_credit
from crunevo.constants import CreditReasons
from datetime import datetime, timedelta, date
import secrets

challenges_bp = Blueprint("challenges", __name__, url_prefix="/desafios")


@challenges_bp.route("/mentor-fantasma")
@login_required
@activated_required
def ghost_mentor():
    """Ghost Mentor Challenge page"""

    if current_user.role != "admin":
        flash("Acceso restringido", "warning")
        return redirect(url_for("feed.feed_home"))
    if not table_exists("ghost_mentor_challenge"):
        flash("Función no disponible", "warning")
        return render_template(
            "challenges/ghost_mentor.html",
            active_challenge=None,
            user_response=None,
            recent_challenges=[],
        )
    # Get active challenge
    active_challenge = GhostMentorChallenge.query.filter(
        GhostMentorChallenge.is_active.is_(True),
        GhostMentorChallenge.end_time > datetime.utcnow(),
    ).first()

    user_response = None
    if active_challenge:
        user_response = GhostMentorResponse.query.filter_by(
            challenge_id=active_challenge.id, user_id=current_user.id
        ).first()

    # Get recent challenges
    recent_challenges = (
        GhostMentorChallenge.query.filter(
            GhostMentorChallenge.end_time < datetime.utcnow()
        )
        .order_by(GhostMentorChallenge.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "challenges/ghost_mentor.html",
        active_challenge=active_challenge,
        user_response=user_response,
        recent_challenges=recent_challenges,
    )


@challenges_bp.route("/mentor-fantasma/responder", methods=["POST"])
@login_required
@activated_required
def submit_ghost_response():
    """Submit response to Ghost Mentor Challenge"""
    challenge_id = request.form.get("challenge_id", type=int)
    response_content = request.form.get("response", "").strip()

    if not challenge_id or not response_content:
        return jsonify({"error": "Datos incompletos"}), 400

    challenge = GhostMentorChallenge.query.get_or_404(challenge_id)

    # Check if challenge is still active
    if not challenge.is_active or challenge.end_time <= datetime.utcnow():
        return jsonify({"error": "El desafío ha expirado"}), 400

    # Check if user already responded
    existing_response = GhostMentorResponse.query.filter_by(
        challenge_id=challenge_id, user_id=current_user.id
    ).first()

    if existing_response:
        return jsonify({"error": "Ya has respondido este desafío"}), 400

    # Evaluate response (simplified - could use AI)
    is_correct = evaluate_ghost_response(response_content, challenge.correct_answer)
    points_earned = (
        challenge.reward_crolars if is_correct else secrets.randbelow(10) + 1
    )

    # Create response
    response = GhostMentorResponse(
        challenge_id=challenge_id,
        user_id=current_user.id,
        response_content=response_content,
        is_correct=is_correct,
        points_earned=points_earned,
    )

    db.session.add(response)

    # Award credits
    add_credit(current_user, points_earned, CreditReasons.EVENTO)

    # Award team points if user is in a team
    from crunevo.routes.league_routes import award_team_points

    award_team_points(current_user.id, "ghost_challenge", points_earned)

    db.session.commit()

    return jsonify(
        {
            "success": True,
            "is_correct": is_correct,
            "points_earned": points_earned,
            "message": "¡Respuesta enviada! Has ganado {} Crolars".format(
                points_earned
            ),
        }
    )


@challenges_bp.route("/pregunta-maestra")
@login_required
@activated_required
def master_question():
    """Master Question page"""
    today = date.today()

    # Get today's question
    question = MasterQuestion.query.filter_by(active_date=today).first()

    user_attempt = None
    if question:
        user_attempt = MasterQuestionAttempt.query.filter_by(
            question_id=question.id, user_id=current_user.id
        ).first()

    # Get recent questions
    recent_questions = (
        MasterQuestion.query.filter(MasterQuestion.active_date < today)
        .order_by(MasterQuestion.active_date.desc())
        .limit(7)
        .all()
    )

    return render_template(
        "challenges/master_question.html",
        question=question,
        user_attempt=user_attempt,
        recent_questions=recent_questions,
    )


@challenges_bp.route("/pregunta-maestra/responder", methods=["POST"])
@login_required
@activated_required
def submit_master_answer():
    """Submit answer to Master Question"""
    question_id = request.form.get("question_id", type=int)
    answer = request.form.get("answer", "").strip()

    if not question_id or not answer:
        return jsonify({"error": "Datos incompletos"}), 400

    question = MasterQuestion.query.get_or_404(question_id)

    # Check if question is already answered
    if question.is_answered:
        return jsonify({"error": "Esta pregunta ya fue respondida correctamente"}), 400

    # Check if user already attempted
    existing_attempt = MasterQuestionAttempt.query.filter_by(
        question_id=question_id, user_id=current_user.id
    ).first()

    if existing_attempt:
        return jsonify({"error": "Ya has intentado responder esta pregunta"}), 400

    # Check if answer is correct
    is_correct = answer.lower().strip() == question.correct_answer.lower().strip()

    # Create attempt
    attempt = MasterQuestionAttempt(
        question_id=question_id,
        user_id=current_user.id,
        answer_given=answer,
        is_correct=is_correct,
    )

    db.session.add(attempt)

    if is_correct:
        # Mark question as answered
        question.is_answered = True
        question.winner_id = current_user.id
        question.answered_at = datetime.utcnow()

        # Award prizes
        add_credit(current_user, question.reward_crolars, CreditReasons.LOGRO)

        # Award badge (could integrate with achievement system)
        from crunevo.utils.achievements import award_achievement

        award_achievement(current_user.id, question.badge_code)

        # Award team points
        from crunevo.routes.league_routes import award_team_points

        award_team_points(current_user.id, "master_question", question.reward_crolars)

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "is_correct": True,
                "message": f"¡Correcto! Has ganado {question.reward_crolars} Crolars y la insignia del día",
            }
        )
    else:
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "is_correct": False,
                "message": "Respuesta incorrecta. ¡Mejor suerte mañana!",
            }
        )


@challenges_bp.route("/api/ghost-mentor/current")
@login_required
def get_current_ghost_challenge():
    """Get current ghost mentor challenge for feed"""
    challenge = GhostMentorChallenge.query.filter(
        GhostMentorChallenge.is_active.is_(True),
        GhostMentorChallenge.end_time > datetime.utcnow(),
    ).first()

    if not challenge:
        return jsonify({"challenge": None})

    # Check if user already responded
    user_response = GhostMentorResponse.query.filter_by(
        challenge_id=challenge.id, user_id=current_user.id
    ).first()

    time_left = (challenge.end_time - datetime.utcnow()).total_seconds()

    return jsonify(
        {
            "challenge": {
                "id": challenge.id,
                "title": challenge.title,
                "description": challenge.description,
                "challenge_content": challenge.challenge_content,
                "reward_crolars": challenge.reward_crolars,
                "difficulty_level": challenge.difficulty_level,
                "time_left": max(0, time_left),
                "has_responded": user_response is not None,
            }
        }
    )


@challenges_bp.route("/api/master-question/current")
@login_required
def get_current_master_question():
    """Get current master question for feed"""
    today = date.today()
    question = MasterQuestion.query.filter_by(active_date=today).first()

    if not question:
        return jsonify({"question": None})

    # Check if user already attempted
    user_attempt = MasterQuestionAttempt.query.filter_by(
        question_id=question.id, user_id=current_user.id
    ).first()

    return jsonify(
        {
            "question": {
                "id": question.id,
                "question_text": question.question_text,
                "category": question.category,
                "difficulty": question.difficulty,
                "reward_crolars": question.reward_crolars,
                "is_answered": question.is_answered,
                "winner": question.winner.username if question.winner else None,
                "has_attempted": user_attempt is not None,
            }
        }
    )


def evaluate_ghost_response(response, correct_answer):
    """Evaluate ghost mentor response (simplified)"""
    if not correct_answer:
        return True  # Open-ended questions are always correct

    # Simple keyword matching
    response_words = set(response.lower().split())
    answer_words = set(correct_answer.lower().split())

    # If 70% of answer words are in response, consider correct
    if len(answer_words) == 0:
        return True

    match_ratio = len(response_words.intersection(answer_words)) / len(answer_words)
    return match_ratio >= 0.7


def create_weekly_ghost_challenge():
    """Create a new weekly ghost mentor challenge"""
    challenges_pool = [
        {
            "title": "Desafío de Programación",
            "description": "El Mentor Fantasma te presenta un algoritmo misterioso",
            "content": "¿Cuál es la complejidad temporal del algoritmo de búsqueda binaria y por qué es más eficiente que la búsqueda lineal?",
            "answer": "O(log n) porque divide el espacio de búsqueda por la mitad en cada iteración",
            "difficulty": "medium",
        },
        {
            "title": "Enigma Matemático",
            "description": "Un problema que desafía tu lógica matemática",
            "content": "Si tienes una función f(x) = x² + 2x + 1, ¿cuál es su forma factorizada y qué nos dice sobre sus raíces?",
            "answer": "(x + 1)² tiene una raíz doble en x = -1",
            "difficulty": "hard",
        },
        {
            "title": "Desafío de Física",
            "description": "Las leyes de la física ocultan secretos",
            "content": "Explica el principio de conservación de la energía y da un ejemplo práctico",
            "answer": "La energía no se crea ni se destruye, solo se transforma",
            "difficulty": "medium",
        },
    ]

    challenge_data = secrets.choice(challenges_pool)

    challenge = GhostMentorChallenge(
        title=challenge_data["title"],
        description=challenge_data["description"],
        challenge_content=challenge_data["content"],
        correct_answer=challenge_data["answer"],
        reward_crolars=secrets.randbelow(31) + 20,
        end_time=datetime.utcnow() + timedelta(days=7),
        difficulty_level=challenge_data["difficulty"],
    )

    db.session.add(challenge)
    db.session.commit()

    return challenge


def create_daily_master_question():
    """Create daily master question"""
    questions_pool = [
        {
            "question": "¿Cuál es el país con mayor biodiversidad del mundo?",
            "answer": "Brasil",
            "category": "geografía",
        },
        {
            "question": "¿En qué año se fundó la Universidad Nacional Mayor de San Marcos?",
            "answer": "1551",
            "category": "historia",
        },
        {
            "question": "¿Cuál es la fórmula química del agua oxigenada?",
            "answer": "H2O2",
            "category": "química",
        },
    ]

    question_data = secrets.choice(questions_pool)
    today = date.today()

    # Check if question already exists for today
    existing = MasterQuestion.query.filter_by(active_date=today).first()
    if existing:
        return existing

    question = MasterQuestion(
        question_text=question_data["question"],
        correct_answer=question_data["answer"],
        category=question_data["category"],
        active_date=today,
    )

    db.session.add(question)
    db.session.commit()

    return question
