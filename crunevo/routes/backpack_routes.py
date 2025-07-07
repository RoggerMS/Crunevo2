from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.knowledge_backpack import (
    KnowledgeBackpack,
    LearningEntry,
    BackpackAchievement,
)
from crunevo.models.note import Note
from crunevo.models.mission import UserMission
from crunevo.utils.helpers import activated_required, table_exists
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from flask import Response

backpack_bp = Blueprint("backpack", __name__, url_prefix="/mochila")


@backpack_bp.route("/")
@login_required
@activated_required
def index():
    """Knowledge Backpack main page"""
    if not table_exists("knowledge_backpack"):
        flash("Función no disponible", "warning")
        return render_template(
            "backpack/index.html",
            backpack=None,
            recent_entries=[],
            achievements=[],
        )
    # Get or create user's backpack
    backpack = KnowledgeBackpack.query.filter_by(user_id=current_user.id).first()
    if not backpack:
        backpack = create_user_backpack(current_user.id)

    # Get user stats
    user_notes = Note.query.filter_by(user_id=current_user.id).count()
    user_missions = UserMission.query.filter_by(user_id=current_user.id).count()
    saved_courses = (
        current_user.saved_courses.count()
        if hasattr(current_user, "saved_courses")
        else 0
    )

    # Update backpack stats
    backpack.total_notes = user_notes
    backpack.total_missions = user_missions
    backpack.total_courses = saved_courses
    db.session.commit()

    # Get recent learning entries
    recent_entries = (
        LearningEntry.query.filter_by(backpack_id=backpack.id)
        .order_by(LearningEntry.created_at.desc())
        .limit(5)
        .all()
    )

    # Get backpack achievements
    achievements = (
        BackpackAchievement.query.filter_by(backpack_id=backpack.id)
        .order_by(BackpackAchievement.earned_at.desc())
        .all()
    )

    return render_template(
        "backpack/index.html",
        backpack=backpack,
        recent_entries=recent_entries,
        achievements=achievements,
    )


@backpack_bp.route("/bitacora")
@login_required
@activated_required
def journal():
    """Learning journal page"""
    backpack = get_or_create_backpack(current_user.id)
    if not backpack:
        flash("Función no disponible", "warning")
        return render_template("backpack/journal.html", backpack=None, entries=[])

    # Get all learning entries
    entries = (
        LearningEntry.query.filter_by(backpack_id=backpack.id)
        .order_by(LearningEntry.created_at.desc())
        .all()
    )

    return render_template("backpack/journal.html", backpack=backpack, entries=entries)


@backpack_bp.route("/nueva-entrada", methods=["GET", "POST"])
@login_required
@activated_required
def new_entry():
    """Create new learning entry"""
    if request.method == "POST":
        backpack = get_or_create_backpack(current_user.id)
        if not backpack:
            flash("Función no disponible", "warning")
            return redirect(url_for("backpack.new_entry"))

        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        entry_type = request.form.get("entry_type", "reflection")
        tags = request.form.get("tags", "").strip()

        if not title or not content:
            flash("Título y contenido son requeridos", "error")
            return redirect(url_for("backpack.new_entry"))

        entry = LearningEntry(
            backpack_id=backpack.id,
            title=title,
            content=content,
            entry_type=entry_type,
            tags=tags,
        )

        db.session.add(entry)

        # Update backpack timestamp
        backpack.last_updated = datetime.utcnow()

        # Check for journal achievements
        check_journal_achievements(backpack.id)

        db.session.commit()

        flash("Entrada agregada exitosamente", "success")
        return redirect(url_for("backpack.journal"))

    return render_template("backpack/new_entry.html")


@backpack_bp.route("/entrada/<int:entry_id>")
@login_required
@activated_required
def view_entry(entry_id):
    """View learning entry"""
    if not table_exists("learning_entry"):
        flash("Función no disponible", "warning")
        return redirect(url_for("backpack.journal"))

    entry = LearningEntry.query.get_or_404(entry_id)

    # Check if user owns this entry
    if entry.backpack.user_id != current_user.id:
        flash("No tienes acceso a esta entrada", "error")
        return redirect(url_for("backpack.journal"))

    return render_template("backpack/view_entry.html", entry=entry)


@backpack_bp.route("/editar-entrada/<int:entry_id>", methods=["GET", "POST"])
@login_required
@activated_required
def edit_entry(entry_id):
    """Edit learning entry"""
    if not table_exists("learning_entry"):
        flash("Función no disponible", "warning")
        return redirect(url_for("backpack.journal"))

    entry = LearningEntry.query.get_or_404(entry_id)

    # Check if user owns this entry
    if entry.backpack.user_id != current_user.id:
        flash("No tienes acceso a esta entrada", "error")
        return redirect(url_for("backpack.journal"))

    if request.method == "POST":
        entry.title = request.form.get("title", "").strip()
        entry.content = request.form.get("content", "").strip()
        entry.entry_type = request.form.get("entry_type", "reflection")
        entry.tags = request.form.get("tags", "").strip()
        entry.updated_at = datetime.utcnow()

        # Update backpack timestamp
        entry.backpack.last_updated = datetime.utcnow()

        db.session.commit()

        flash("Entrada actualizada exitosamente", "success")
        return redirect(url_for("backpack.view_entry", entry_id=entry_id))

    return render_template("backpack/edit_entry.html", entry=entry)


@backpack_bp.route("/exportar-pdf")
@login_required
@activated_required
def export_pdf():
    """Export learning journal to PDF"""
    backpack = get_or_create_backpack(current_user.id)
    if not backpack:
        flash("Función no disponible", "warning")
        return redirect(url_for("backpack.journal"))
    entries = (
        LearningEntry.query.filter_by(backpack_id=backpack.id)
        .order_by(LearningEntry.created_at.desc())
        .all()
    )

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph(
        f"Bitácora de Aprendizaje - {current_user.username}", styles["Title"]
    )
    story.append(title)
    story.append(Spacer(1, 12))

    # Stats
    stats_text = f"""
    <b>Estadísticas:</b><br/>
    • Apuntes subidos: {backpack.total_notes}<br/>
    • Cursos completados: {backpack.total_courses}<br/>
    • Misiones completadas: {backpack.total_missions}<br/>
    • Entradas en bitácora: {len(entries)}<br/>
    """
    stats = Paragraph(stats_text, styles["Normal"])
    story.append(stats)
    story.append(Spacer(1, 20))

    # Entries
    for entry in entries:
        entry_title = Paragraph(f"<b>{entry.title}</b>", styles["Heading2"])
        story.append(entry_title)

        entry_meta = Paragraph(
            f"Tipo: {entry.entry_type} | Fecha: {entry.created_at.strftime('%d/%m/%Y %H:%M')}",
            styles["Normal"],
        )
        story.append(entry_meta)

        if entry.tags:
            tags = Paragraph(f"Etiquetas: {entry.tags}", styles["Normal"])
            story.append(tags)

        content = Paragraph(entry.content.replace("\n", "<br/>"), styles["Normal"])
        story.append(content)
        story.append(Spacer(1, 20))

    doc.build(story)
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=bitacora_{current_user.username}.pdf"
        },
    )


@backpack_bp.route("/api/stats")
@login_required
def get_stats():
    """Get backpack statistics"""
    backpack = get_or_create_backpack(current_user.id)
    if not backpack:
        return jsonify({"error": "unavailable"}), 404

    # Get monthly entry count
    from sqlalchemy import extract

    monthly_entries = (
        db.session.query(
            extract("month", LearningEntry.created_at).label("month"),
            db.func.count(LearningEntry.id).label("count"),
        )
        .filter_by(backpack_id=backpack.id)
        .group_by(extract("month", LearningEntry.created_at))
        .all()
    )

    # Get entry types distribution
    entry_types = (
        db.session.query(
            LearningEntry.entry_type, db.func.count(LearningEntry.id).label("count")
        )
        .filter_by(backpack_id=backpack.id)
        .group_by(LearningEntry.entry_type)
        .all()
    )

    return jsonify(
        {
            "monthly_entries": [
                {"month": m.month, "count": m.count} for m in monthly_entries
            ],
            "entry_types": [
                {"type": t.entry_type, "count": t.count} for t in entry_types
            ],
            "total_achievements": len(backpack.achievements),
        }
    )


def get_or_create_backpack(user_id):
    """Get or create user's backpack"""
    if not table_exists("knowledge_backpack"):
        return None

    backpack = KnowledgeBackpack.query.filter_by(user_id=user_id).first()
    if not backpack:
        backpack = create_user_backpack(user_id)
    return backpack


def create_user_backpack(user_id):
    """Create new backpack for user"""
    backpack = KnowledgeBackpack(user_id=user_id)
    db.session.add(backpack)
    db.session.commit()
    return backpack


def check_journal_achievements(backpack_id):
    """Check and award journal achievements"""
    entry_count = LearningEntry.query.filter_by(backpack_id=backpack_id).count()

    achievements_to_check = [
        (1, "first_entry", "Primera Entrada", "Tu primera reflexión académica"),
        (5, "consistent_learner", "Aprendiz Constante", "5 entradas en tu bitácora"),
        (10, "dedicated_student", "Estudiante Dedicado", "10 entradas completadas"),
        (25, "learning_master", "Maestro del Aprendizaje", "25 entradas de reflexión"),
        (
            50,
            "knowledge_keeper",
            "Guardián del Conocimiento",
            "50 entradas en tu bitácora",
        ),
    ]

    for threshold, code, title, description in achievements_to_check:
        if entry_count >= threshold:
            # Check if achievement already exists
            existing = BackpackAchievement.query.filter_by(
                backpack_id=backpack_id, achievement_type=code
            ).first()

            if not existing:
                achievement = BackpackAchievement(
                    backpack_id=backpack_id,
                    achievement_type=code,
                    title=title,
                    description=description,
                )
                db.session.add(achievement)

    db.session.commit()
