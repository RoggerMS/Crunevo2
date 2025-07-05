from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Course, SavedCourse
from crunevo.utils import record_activity
from sqlalchemy import desc

course_bp = Blueprint("courses", __name__, url_prefix="/cursos")


@course_bp.route("/")
@activated_required
def list_courses():
    """Lista todos los cursos disponibles"""
    category = request.args.get("categoria")
    difficulty = request.args.get("dificultad")
    search = request.args.get("q", "").strip()

    query = Course.query

    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(Course.title.ilike(f"%{search}%"))

    courses = query.order_by(desc(Course.created_at)).all()

    # Get categories and difficulties for filters
    categories = (
        db.session.query(Course.category)
        .distinct()
        .filter(Course.category.isnot(None))
        .all()
    )
    categories = [cat[0] for cat in categories]

    difficulties = ["Básico", "Intermedio", "Avanzado"]

    # Get featured courses
    featured_courses = Course.query.filter_by(is_featured=True).limit(3).all()

    # Get user's saved courses
    saved_course_ids = []
    if current_user.is_authenticated:
        saved_courses = SavedCourse.query.filter_by(user_id=current_user.id).all()
        saved_course_ids = [sc.course_id for sc in saved_courses]

    return render_template(
        "courses/list.html",
        courses=courses,
        categories=categories,
        difficulties=difficulties,
        featured_courses=featured_courses,
        saved_course_ids=saved_course_ids,
        current_category=category,
        current_difficulty=difficulty,
        current_search=search,
    )


@course_bp.route("/<int:course_id>")
@activated_required
def view_course(course_id):
    """Vista detallada de un curso"""
    course = Course.query.get_or_404(course_id)

    # Increment view count
    course.views += 1
    db.session.commit()

    # Check if user has saved this course
    is_saved = False
    if current_user.is_authenticated:
        is_saved = (
            SavedCourse.query.filter_by(
                user_id=current_user.id, course_id=course.id
            ).first()
            is not None
        )

    # Get related courses
    related_courses = (
        Course.query.filter(Course.category == course.category, Course.id != course.id)
        .limit(4)
        .all()
    )

    return render_template(
        "courses/detail.html",
        course=course,
        is_saved=is_saved,
        related_courses=related_courses,
    )


@course_bp.route("/save/<int:course_id>", methods=["POST"])
@activated_required
def toggle_save_course(course_id):
    """Guardar o quitar curso de guardados"""
    course = Course.query.get_or_404(course_id)

    saved_course = SavedCourse.query.filter_by(
        user_id=current_user.id, course_id=course.id
    ).first()

    if saved_course:
        db.session.delete(saved_course)
        action = "removed"
        message = "Curso eliminado de guardados"
    else:
        saved_course = SavedCourse(user_id=current_user.id, course_id=course.id)
        db.session.add(saved_course)
        action = "saved"
        message = "Curso guardado exitosamente"

    db.session.commit()
    record_activity(f"course_{action}", course.id, "course")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"action": action, "message": message})

    flash(message, "success")
    return redirect(url_for("courses.view_course", course_id=course.id))


@course_bp.route("/mis-cursos")
@activated_required
def my_saved_courses():
    """Cursos guardados por el usuario"""
    saved_courses = (
        db.session.query(Course)
        .join(SavedCourse)
        .filter(SavedCourse.user_id == current_user.id)
        .order_by(desc(SavedCourse.saved_at))
        .all()
    )

    return render_template("courses/saved.html", courses=saved_courses)


@course_bp.route("/api/search")
@activated_required
def api_search_courses():
    """API para búsqueda de cursos"""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    courses = Course.query.filter(Course.title.ilike(f"%{q}%")).limit(10).all()

    results = []
    for course in courses:
        results.append(
            {
                "id": course.id,
                "title": course.title,
                "creator": course.creator.username,
                "category": course.category,
                "url": url_for("courses.view_course", course_id=course.id),
            }
        )

    return jsonify(results)
