import os
import re
import bleach
import cloudinary.uploader
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    current_app,
    abort,
)
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, asc
from sqlalchemy.exc import ProgrammingError, OperationalError
from datetime import datetime
from crunevo.extensions import db
from crunevo.models.forum import (
    ForumQuestion,
    ForumAnswer,
    ForumTag,
    ForumReport,
    question_tags,
    answer_votes,
)
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons

forum_bp = Blueprint("forum", __name__)

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "ul",
    "ol",
    "li",
    "a",
    "img",
    "code",
    "pre",
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
]
ALLOWED_ATTRS = {
    "a": ["href", "target"],
    "img": ["src", "alt", "style"],
    "code": ["class"],
    "pre": ["class"],
}

CATEGORIES = [
    "Matemáticas",
    "Ciencias",
    "Lenguas",
    "Historia",
    "Tecnología",
    "Arte",
    "Otros",
]

DIFFICULTY_LEVELS = [
    ("basico", "🟢 Básico"),
    ("intermedio", "🟡 Intermedio"),
    ("avanzado", "🔴 Avanzado"),
]

GRADE_LEVELS = [
    ("primaria-1-3", "1° - 3° Primaria"),
    ("primaria-4-6", "4° - 6° Primaria"),
    ("secundaria-1-3", "1° - 3° Secundaria"),
    ("secundaria-4-5", "4° - 5° Secundaria"),
    ("preparatoria", "Preparatoria"),
    ("universidad", "Universidad"),
]


class EmptyPagination:
    """Fallback pagination object when DB queries fail"""

    def __init__(self, page=1, per_page=15):
        self.page = page
        self.per_page = per_page
        self.items = []
        self.total = 0
        self.pages = 0
        self.has_prev = False
        self.has_next = False
        self.prev_num = None
        self.next_num = None

    def iter_pages(self):
        return []


def ensure_forum_tables(page=1, per_page=15):
    """Check forum tables exist, returning EmptyPagination if missing."""
    try:
        ForumQuestion.query.first()
    except ProgrammingError:
        current_app.logger.error(
            "Forum tables missing or migrations not applied", exc_info=True
        )
        db.session.rollback()
        return EmptyPagination(page, per_page)
    return None


@forum_bp.route("/foro")
def list_questions():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category", "")
    difficulty = request.args.get("difficulty", "")
    grade_level = request.args.get("grade_level", "")
    tags = request.args.get("tags", "")
    sort_by = request.args.get("sort", "recent")  # recent, popular, urgent, solved
    search = request.args.get("search", "")
    context_type = request.args.get("context", "")

    table_check = ensure_forum_tables(page)
    if isinstance(table_check, EmptyPagination):
        abort(
            500,
            description="Forum database schema missing or migrations not applied",
        )

    # Build base query
    query = ForumQuestion.query

    # Apply filters
    if category:
        query = query.filter_by(category=category)

    if difficulty:
        query = query.filter_by(difficulty_level=difficulty)

    if grade_level:
        query = query.filter_by(grade_level=grade_level)

    if context_type:
        query = query.filter_by(context_type=context_type)

    if search:
        search_filter = or_(
            ForumQuestion.title.contains(search), ForumQuestion.content.contains(search)
        )
        query = query.filter(search_filter)

    if tags:
        tag_names = [tag.strip() for tag in tags.split(",")]
        query = query.join(ForumQuestion.tags).filter(ForumTag.name.in_(tag_names))

    # Apply sorting
    if sort_by == "popular":
        query = (
            query.outerjoin(ForumAnswer)
            .group_by(ForumQuestion.id)
            .order_by(desc(db.func.count(ForumAnswer.id)), desc(ForumQuestion.views))
        )
    elif sort_by == "urgent":
        query = query.filter_by(is_urgent=True).order_by(desc(ForumQuestion.created_at))
    elif sort_by == "solved":
        query = query.filter_by(is_solved=True).order_by(desc(ForumQuestion.updated_at))
    elif sort_by == "unanswered":
        query = query.filter(~ForumQuestion.answers.any()).order_by(
            desc(ForumQuestion.created_at)
        )
    elif sort_by == "bounty":
        query = query.filter(ForumQuestion.bounty_points > 0).order_by(
            desc(ForumQuestion.bounty_points)
        )
    else:  # recent
        query = query.order_by(desc(ForumQuestion.created_at))

    try:
        questions = query.paginate(page=page, per_page=15, error_out=False)

        # Get popular tags for sidebar
        popular_tags = (
            db.session.query(ForumTag)
            .join(question_tags)
            .group_by(ForumTag.id)
            .order_by(db.func.count(question_tags.c.question_id).desc())
            .limit(10)
            .all()
        )

        # Get statistics
        stats = {
            "total_questions": ForumQuestion.query.count(),
            "solved_questions": ForumQuestion.query.filter_by(is_solved=True).count(),
            "urgent_questions": ForumQuestion.query.filter_by(is_urgent=True).count(),
            "questions_today": ForumQuestion.query.filter(
                ForumQuestion.created_at
                >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
        }
    except (ProgrammingError, OperationalError):
        current_app.logger.error("Error loading forum questions", exc_info=True)
        db.session.rollback()
        questions = EmptyPagination(page, 15)
        popular_tags = []
        stats = {
            "total_questions": 0,
            "solved_questions": 0,
            "urgent_questions": 0,
            "questions_today": 0,
        }

    return render_template(
        "forum/list.html",
        questions=questions,
        categories=CATEGORIES,
        difficulty_levels=DIFFICULTY_LEVELS,
        grade_levels=GRADE_LEVELS,
        popular_tags=popular_tags,
        current_category=category,
        current_difficulty=difficulty,
        current_grade_level=grade_level,
        current_tags=tags,
        current_sort=sort_by,
        current_search=search,
        current_context=context_type,
        stats=stats,
    )


@forum_bp.route("/foro/pregunta/<int:question_id>")
def view_question(question_id):
    question = ForumQuestion.query.get_or_404(question_id)

    # Increment views (but not for the author)
    if not current_user.is_authenticated or current_user.id != question.author_id:
        question.views += 1
        db.session.commit()

    # Get answers with improved sorting
    answers_query = ForumAnswer.query.filter_by(question_id=question_id)

    sort_answers = request.args.get("sort_answers", "best")
    if sort_answers == "newest":
        answers_query = answers_query.order_by(desc(ForumAnswer.created_at))
    elif sort_answers == "oldest":
        answers_query = answers_query.order_by(asc(ForumAnswer.created_at))
    else:  # best (default)
        answers_query = answers_query.order_by(
            desc(ForumAnswer.is_accepted),
            desc(ForumAnswer.votes),
            desc(ForumAnswer.helpful_count),
            asc(ForumAnswer.created_at),
        )

    answers = answers_query.all()

    # Get related questions
    related_questions = (
        ForumQuestion.query.filter(
            and_(
                ForumQuestion.id != question_id,
                ForumQuestion.category == question.category,
            )
        )
        .order_by(desc(ForumQuestion.views))
        .limit(5)
        .all()
    )

    # Check if user has bookmarked this question
    is_bookmarked = False
    if current_user.is_authenticated:
        is_bookmarked = question in current_user.bookmarked_questions

    return render_template(
        "forum/question.html",
        question=question,
        answers=answers,
        related_questions=related_questions,
        is_bookmarked=is_bookmarked,
        sort_answers=sort_answers,
    )


@forum_bp.route("/foro/hacer-pregunta", methods=["GET", "POST"])
@login_required
def ask_question():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        content = bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
        plain_text = bleach.clean(content, tags=[], strip=True)
        if len(re.sub(r"\s+", "", plain_text)) < 20:
            flash("La descripci\u00f3n debe tener al menos 20 caracteres", "error")
            return redirect(url_for("forum.ask_question"))
        category = request.form.get("category")
        difficulty_level = request.form.get("difficulty_level", "intermedio")
        grade_level = request.form.get("grade_level", "")
        subject_area = request.form.get("subject_area", "")
        context_type = request.form.get("context_type", "general")
        is_urgent = request.form.get("is_urgent") == "on"
        bounty_points = int(request.form.get("bounty_points", 0))

        # Parse homework deadline if provided
        homework_deadline = None
        deadline_str = request.form.get("homework_deadline")
        if deadline_str:
            try:
                homework_deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                pass

        # Get selected tags
        tag_names = request.form.getlist("tags")

        if not title or not content or not category:
            flash("Todos los campos obligatorios son requeridos", "error")
            return redirect(url_for("forum.ask_question"))

        # Validate bounty points
        if bounty_points > 0 and current_user.points < bounty_points:
            flash(
                f"No tienes suficientes puntos para ofrecer {bounty_points} puntos de recompensa",
                "error",
            )
            return redirect(url_for("forum.ask_question"))

        question = ForumQuestion(
            title=title,
            content=content,
            category=category,
            difficulty_level=difficulty_level,
            grade_level=grade_level,
            subject_area=subject_area,
            context_type=context_type,
            is_urgent=is_urgent,
            bounty_points=bounty_points,
            homework_deadline=homework_deadline,
            author_id=current_user.id,
        )

        db.session.add(question)
        db.session.flush()  # Get the question ID

        # Add tags
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if tag_name:
                tag = ForumTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = ForumTag(name=tag_name)
                    db.session.add(tag)
                question.tags.append(tag)

        # Deduct bounty points from user
        if bounty_points > 0:
            current_user.points -= bounty_points

        db.session.commit()

        # Award credits for asking
        credits_awarded = 3
        if is_urgent:
            credits_awarded += 2
        if bounty_points > 0:
            credits_awarded += 2

        add_credit(
            current_user,
            credits_awarded,
            CreditReasons.ACTIVIDAD_SOCIAL,
            related_id=question.id,
        )

        flash("¡Pregunta publicada exitosamente!")
        return redirect(url_for("forum.view_question", question_id=question.id))

    # GET request - show form
    all_tags = ForumTag.query.order_by(ForumTag.name).all()

    return render_template(
        "forum/ask.html",
        categories=CATEGORIES,
        difficulty_levels=DIFFICULTY_LEVELS,
        grade_levels=GRADE_LEVELS,
        all_tags=all_tags,
    )


@forum_bp.route("/foro/responder/<int:question_id>", methods=["POST"])
@login_required
def answer_question(question_id):
    # Ensure the question exists
    ForumQuestion.query.get_or_404(question_id)
    content = request.form.get("content")
    content = bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
    confidence_level = request.form.get("confidence_level", "medium")
    explanation_quality = request.form.get("explanation_quality", "good")

    if not content:
        flash("El contenido de la respuesta es requerido", "error")
        return redirect(url_for("forum.view_question", question_id=question_id))

    # Auto-detect answer features
    word_count = len(content.split())
    has_step_by_step = any(
        keyword in content.lower()
        for keyword in ["paso", "primero", "segundo", "luego", "después", "finalmente"]
    )
    has_visual_aids = (
        "<img" in content
        or "gráfico" in content.lower()
        or "diagrama" in content.lower()
    )
    contains_formulas = any(
        char in content for char in ["∑", "∫", "√", "π", "α", "β", "γ", "∆"]
    )
    contains_code = "<code>" in content or "<pre>" in content or "```" in content

    answer = ForumAnswer(
        content=content,
        question_id=question_id,
        author_id=current_user.id,
        confidence_level=confidence_level,
        explanation_quality=explanation_quality,
        word_count=word_count,
        estimated_reading_time=max(1, word_count // 200),
        has_step_by_step=has_step_by_step,
        has_visual_aids=has_visual_aids,
        contains_formulas=contains_formulas,
        contains_code=contains_code,
    )

    db.session.add(answer)
    db.session.commit()

    # Award credits for answering
    credits_awarded = 5
    if has_step_by_step:
        credits_awarded += 3
    if has_visual_aids:
        credits_awarded += 2
    if word_count > 200:
        credits_awarded += 2

    add_credit(
        current_user,
        credits_awarded,
        CreditReasons.ACTIVIDAD_SOCIAL,
        related_id=answer.id,
    )

    flash("¡Respuesta publicada exitosamente!")
    return redirect(url_for("forum.view_question", question_id=question_id))


@forum_bp.route("/foro/respuesta/<int:answer_id>/votar", methods=["POST"])
@login_required
def vote_answer(answer_id):
    answer = ForumAnswer.query.get_or_404(answer_id)
    data = request.get_json()
    vote_type = data.get("vote_type")
    is_helpful = data.get("is_helpful", False)

    # Check if user has already voted
    existing_vote = db.session.execute(
        answer_votes.select().where(
            answer_votes.c.user_id == current_user.id,
            answer_votes.c.answer_id == answer_id,
        )
    ).first()

    if existing_vote:
        # Remove existing vote
        db.session.execute(
            answer_votes.delete().where(
                answer_votes.c.user_id == current_user.id,
                answer_votes.c.answer_id == answer_id,
            )
        )

        # Adjust vote counts
        if existing_vote.vote_type == "up":
            answer.votes -= 1
        elif existing_vote.vote_type == "down":
            answer.votes -= 1

    # Add new vote if different from existing
    if not existing_vote or existing_vote.vote_type != vote_type:
        db.session.execute(
            answer_votes.insert().values(
                user_id=current_user.id, answer_id=answer_id, vote_type=vote_type
            )
        )

        if vote_type == "up":
            answer.votes += 1
        elif vote_type == "down":
            answer.votes -= 1

    # Handle helpful votes separately
    if is_helpful and vote_type == "up":
        answer.helpful_count += 1

    db.session.commit()

    return jsonify(
        {"success": True, "votes": answer.votes, "helpful_count": answer.helpful_count}
    )


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

    # Award bounty points to answerer if applicable
    if question.bounty_points > 0:
        answer.author.points += question.bounty_points
        question.bounty_points = 0  # Bounty claimed

    db.session.commit()

    # Award extra credits to answerer
    add_credit(answer.author, 15, CreditReasons.ACTIVIDAD_SOCIAL, related_id=answer.id)

    return jsonify({"success": True})


@forum_bp.route("/foro/pregunta/<int:question_id>/bookmark", methods=["POST"])
@login_required
def bookmark_question(question_id):
    question = ForumQuestion.query.get_or_404(question_id)

    if question in current_user.bookmarked_questions:
        current_user.bookmarked_questions.remove(question)
        bookmarked = False
    else:
        current_user.bookmarked_questions.append(question)
        bookmarked = True

    db.session.commit()

    return jsonify({"success": True, "bookmarked": bookmarked})


@forum_bp.route("/foro/buscar")
def search():
    """Advanced search endpoint"""
    query = request.args.get("q", "")
    category = request.args.get("category", "")
    difficulty = request.args.get("difficulty", "")
    has_answers = request.args.get("has_answers", "")
    is_solved = request.args.get("is_solved", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    # Build search results
    search_query = ForumQuestion.query

    if query:
        search_filter = or_(
            ForumQuestion.title.contains(query), ForumQuestion.content.contains(query)
        )
        search_query = search_query.filter(search_filter)

    if category:
        search_query = search_query.filter_by(category=category)

    if difficulty:
        search_query = search_query.filter_by(difficulty_level=difficulty)

    if has_answers == "yes":
        search_query = search_query.filter(ForumQuestion.answers.any())
    elif has_answers == "no":
        search_query = search_query.filter(~ForumQuestion.answers.any())

    if is_solved == "yes":
        search_query = search_query.filter_by(is_solved=True)
    elif is_solved == "no":
        search_query = search_query.filter_by(is_solved=False)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            search_query = search_query.filter(
                ForumQuestion.created_at >= date_from_obj
            )
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            search_query = search_query.filter(ForumQuestion.created_at <= date_to_obj)
        except ValueError:
            pass

    questions = search_query.order_by(desc(ForumQuestion.created_at)).limit(50).all()

    return render_template(
        "forum/search_results.html", questions=questions, search_params=request.args
    )


@forum_bp.route("/foro/reportar", methods=["POST"])
@login_required
def report_content():
    """Report inappropriate content"""
    data = request.get_json()
    question_id = data.get("question_id")
    answer_id = data.get("answer_id")
    reason = data.get("reason")
    description = data.get("description", "")

    if not reason or (not question_id and not answer_id):
        return jsonify({"error": "Datos incompletos"}), 400

    report = ForumReport(
        reporter_id=current_user.id,
        reported_question_id=question_id,
        reported_answer_id=answer_id,
        reason=reason,
        description=description,
    )

    db.session.add(report)
    db.session.commit()

    return jsonify({"success": True, "message": "Reporte enviado exitosamente"})


@forum_bp.route("/api/upload", methods=["POST"])
@login_required
def upload_image():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file"}), 400
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}:
        return jsonify({"error": "Tipo de archivo no permitido"}), 400
    if request.content_length and request.content_length > 5 * 1024 * 1024:  # 5MB limit
        return jsonify({"error": "Archivo demasiado grande"}), 400
    cloud_url = current_app.config.get("CLOUDINARY_URL")
    try:
        if cloud_url:
            res = cloudinary.uploader.upload(file, resource_type="image")
            url = res["secure_url"]
        else:
            filename = secure_filename(file.filename)
            folder = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, filename)
            file.save(path)
            url = path
    except Exception:
        current_app.logger.exception("Error al subir imagen del foro")
        return jsonify({"error": "Upload failed"}), 500
    return jsonify({"url": url})


@forum_bp.route("/api/tags/autocomplete")
def tags_autocomplete():
    """Get tag suggestions for autocomplete"""
    query = request.args.get("q", "")
    tags = ForumTag.query.filter(ForumTag.name.contains(query)).limit(10).all()
    return jsonify(
        [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in tags]
    )


@forum_bp.route("/api/stats")
def forum_stats():
    """Get forum statistics for dashboard"""
    stats = {
        "total_questions": ForumQuestion.query.count(),
        "solved_questions": ForumQuestion.query.filter_by(is_solved=True).count(),
        "total_answers": ForumAnswer.query.count(),
        "active_users_today": db.session.query(ForumQuestion.author_id)
        .filter(
            ForumQuestion.created_at
            >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        .distinct()
        .count(),
        "categories": {},
    }

    for category in CATEGORIES:
        stats["categories"][category] = ForumQuestion.query.filter_by(
            category=category
        ).count()

    return jsonify(stats)
