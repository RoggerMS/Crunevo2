from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.forum import ForumQuestion, ForumAnswer
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons

forum_bp = Blueprint("forum", __name__)


@forum_bp.route("/foro")
def list_questions():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "")

    query = ForumQuestion.query
    if category:
        query = query.filter_by(category=category)

    questions = query.order_by(ForumQuestion.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    categories = [
        "Matemáticas",
        "Ciencias",
        "Lenguas",
        "Historia",
        "Tecnología",
        "Arte",
        "Otros",
    ]

    return render_template(
        "forum/list.html",
        questions=questions,
        categories=categories,
        current_category=category,
    )


@forum_bp.route("/foro/pregunta/<int:question_id>")
def view_question(question_id):
    question = ForumQuestion.query.get_or_404(question_id)

    # Increment views
    question.views += 1
    db.session.commit()

    answers = (
        ForumAnswer.query.filter_by(question_id=question_id)
        .order_by(
            ForumAnswer.is_accepted.desc(),
            ForumAnswer.votes.desc(),
            ForumAnswer.created_at.asc(),
        )
        .all()
    )

    return render_template("forum/question.html", question=question, answers=answers)


@forum_bp.route("/foro/hacer-pregunta", methods=["GET", "POST"])
@login_required
def ask_question():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")

        if not title or not content or not category:
            flash("Todos los campos son requeridos", "error")
            return redirect(url_for("forum.ask_question"))

        question = ForumQuestion(
            title=title, content=content, category=category, author_id=current_user.id
        )

        db.session.add(question)
        db.session.commit()

        # Award credits for asking
        add_credit(
            current_user, 3, CreditReasons.ACTIVIDAD_SOCIAL, related_id=question.id
        )

        flash("¡Pregunta publicada exitosamente!")
        return redirect(url_for("forum.view_question", question_id=question.id))

    categories = [
        "Matemáticas",
        "Ciencias",
        "Lenguas",
        "Historia",
        "Tecnología",
        "Arte",
        "Otros",
    ]
    return render_template("forum/ask.html", categories=categories)


@forum_bp.route("/foro/responder/<int:question_id>", methods=["POST"])
@login_required
def answer_question(question_id):
    ForumQuestion.query.get_or_404(question_id)
    content = request.form.get("content")

    if not content:
        flash("El contenido de la respuesta es requerido", "error")
        return redirect(url_for("forum.view_question", question_id=question_id))

    answer = ForumAnswer(
        content=content, question_id=question_id, author_id=current_user.id
    )

    db.session.add(answer)
    db.session.commit()

    # Award credits for answering
    add_credit(current_user, 5, CreditReasons.ACTIVIDAD_SOCIAL, related_id=answer.id)

    flash("¡Respuesta publicada exitosamente!")
    return redirect(url_for("forum.view_question", question_id=question_id))


@forum_bp.route("/foro/respuesta/<int:answer_id>/votar", methods=["POST"])
@login_required
def vote_answer(answer_id):
    answer = ForumAnswer.query.get_or_404(answer_id)
    data = request.get_json()
    vote_type = data.get("vote_type")

    if vote_type == "up":
        answer.votes += 1
    elif vote_type == "down":
        answer.votes -= 1

    db.session.commit()
    return jsonify({"success": True, "votes": answer.votes})


@forum_bp.route("/foro/respuesta/<int:answer_id>/aceptar", methods=["POST"])
@login_required
def accept_answer(answer_id):
    answer = ForumAnswer.query.get_or_404(answer_id)
    question = answer.question

    # Only question author can accept answers
    if current_user.id != question.author_id:
        return jsonify({"error": "No autorizado"}), 403

    # Unmark other answers as accepted
    ForumAnswer.query.filter_by(question_id=question.id).update({"is_accepted": False})

    # Mark this answer as accepted
    answer.is_accepted = True
    question.is_solved = True

    db.session.commit()

    # Award extra credits to answerer
    add_credit(answer.author, 10, CreditReasons.ACTIVIDAD_SOCIAL, related_id=answer.id)

    return jsonify({"success": True})
