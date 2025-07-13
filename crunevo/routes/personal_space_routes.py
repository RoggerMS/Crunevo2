# fmt: off
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
)
# fmt: on
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.block import Block
from crunevo.utils.helpers import activated_required
from datetime import datetime
import json  # noqa: F401

personal_space_bp = Blueprint(
    "personal_space", __name__, url_prefix="/espacio-personal"
)


@personal_space_bp.route("/")
@login_required
@activated_required
def index():
    """Main personal space dashboard"""
    blocks = (
        Block.query.filter_by(user_id=current_user.id)
        .order_by(Block.order_index.asc(), Block.created_at.asc())
        .all()
    )

    # Get smart suggestions
    suggestions = get_smart_suggestions()

    return render_template(
        "personal_space/index.html",
        blocks=blocks,
        suggestions=suggestions,
        get_default_icon=get_default_icon,
    )


@personal_space_bp.route("/api/blocks", methods=["GET"])
@login_required
@activated_required
def get_blocks():
    """API endpoint to get all user blocks"""
    blocks = (
        Block.query.filter_by(user_id=current_user.id)
        .order_by(Block.order_index.asc())
        .all()
    )

    return jsonify({"success": True, "blocks": [block.to_dict() for block in blocks]})


@personal_space_bp.route("/api/blocks", methods=["POST"])
@login_required
@activated_required
def create_block():
    """Create a new personal block"""
    data = request.get_json() or {}

    if not data or "type" not in data:
        return jsonify({"success": False, "message": "Tipo de bloque requerido"}), 400

    max_order = (
        db.session.query(db.func.max(Block.order_index))
        .filter_by(user_id=current_user.id)
        .scalar()
        or 0
    )

    metadata = data.get("metadata", {})
    metadata.setdefault("color", data.get("color", "indigo"))
    metadata.setdefault("icon", data.get("icon", get_default_icon(data["type"])))

    block = Block(
        user_id=current_user.id,
        type=data["type"],
        title=data.get("title", ""),
        content=data.get("content", ""),
        order_index=max_order + 1,
    )
    block.set_metadata(metadata)

    # Set default metadata based on block type
    if data["type"] == "lista":
        metadata.setdefault("tasks", [])
    elif data["type"] == "meta":
        metadata.setdefault("progress", 0)
        metadata.setdefault("target_date", "")
    elif data["type"] == "recordatorio":
        metadata.setdefault("due_date", "")
        metadata.setdefault("priority", "medium")
    elif data["type"] == "frase":
        metadata.setdefault("author", "")
        metadata.setdefault("category", "motivacional")
    elif data["type"] == "enlace":
        metadata.setdefault("url", "")
        metadata.setdefault("description", "")
    elif data["type"] == "tarea":
        metadata.update(
            {
                "completed": False,
                "priority": "medium",
                "due_date": "",
                "category": "",
                "attachments": [],
            }
        )
    elif data["type"] == "kanban":
        metadata.setdefault("columns", {"Por hacer": [], "En curso": [], "Hecho": []})
    elif data["type"] == "objetivo":
        metadata.update(
            {
                "status": "no_iniciada",
                "progress": 0,
                "deadline": "",
                "frequency": "una_vez",
                "category": "academica",
            }
        )
    elif data["type"] == "bloque":
        metadata.setdefault("grouped_blocks", [])
        metadata.setdefault("subject", "")
        metadata.setdefault("expandable", True)

    db.session.add(block)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "block": block.to_dict(),
            "message": "Bloque creado exitosamente",
        }
    )


@personal_space_bp.route("/api/blocks/<int:block_id>", methods=["PUT"])
@login_required
@activated_required
def update_block(block_id):
    """Update an existing block"""
    block = Block.query.filter_by(id=block_id, user_id=current_user.id).first()

    if not block:
        return jsonify({"success": False, "message": "Bloque no encontrado"}), 404

    data = request.get_json()

    # Update basic fields
    if "title" in data:
        block.title = data["title"]
    if "content" in data:
        block.content = data["content"]
    if "is_featured" in data:
        block.is_featured = data["is_featured"]

    # Update metadata
    if "metadata" in data:
        metadata = block.get_metadata()
        metadata.update(data["metadata"])
        block.set_metadata(metadata)

    block.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(
        {"success": True, "block": block.to_dict(), "message": "Bloque actualizado"}
    )


@personal_space_bp.route("/api/blocks/<int:block_id>", methods=["DELETE"])
@login_required
@activated_required
def delete_block(block_id):
    """Delete a block"""
    block = Block.query.filter_by(id=block_id, user_id=current_user.id).first()

    if not block:
        return jsonify({"success": False, "message": "Bloque no encontrado"}), 404

    db.session.delete(block)
    db.session.commit()

    return jsonify({"success": True, "message": "Bloque eliminado"})


@personal_space_bp.route("/api/blocks/reorder", methods=["POST"])
@login_required
@activated_required
def reorder_blocks():
    """Update block order positions"""
    data = request.get_json()
    block_orders = data.get("blocks", [])

    for item in block_orders:
        block = Block.query.filter_by(id=item["id"], user_id=current_user.id).first()

        if block:
            block.order_index = item["position"]

    db.session.commit()

    return jsonify({"success": True, "message": "Orden actualizado"})


@personal_space_bp.route("/api/create-block", methods=["POST"])
@login_required
@activated_required
def api_create_block_simple():
    """Create a simple Block record"""
    data = request.get_json() or {}

    block = Block(
        user_id=current_user.id,
        type=data.get("type"),
        title=data.get("title", "Nuevo bloque"),
        content=data.get("content", ""),
        order_index=data.get("order_index", 0),
    )
    block.set_metadata(data.get("metadata", {}))
    db.session.add(block)
    db.session.commit()
    return jsonify({"success": True, "block": block.to_dict()})


@personal_space_bp.route("/api/suggestions")
@login_required
@activated_required
def api_suggestions():
    """Get smart suggestions for the user"""
    suggestions = get_smart_suggestions()
    return jsonify({"success": True, "suggestions": suggestions})


def get_smart_suggestions():
    """Generate smart suggestions based on user activity"""
    suggestions = []

    # Check if user has any goals this week
    recent_goals = (
        Block.query.filter_by(user_id=current_user.id)
        .filter(Block.type.in_(["meta", "objetivo"]))
        .filter(
            Block.created_at
            >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        .count()
    )

    if recent_goals == 0:
        suggestions.append(
            {
                "type": "goal",
                "title": "🎯 Establece un objetivo académico",
                "message": "Define metas semanales o mensuales para mejorar tu rendimiento",
                "action": "create_objetivo_block",
            }
        )

    # Check for overdue tasks and reminders
    overdue_items = (
        Block.query.filter_by(user_id=current_user.id)
        .filter(Block.type.in_(["recordatorio", "tarea"]))
        .all()
    )

    overdue_count = sum(1 for item in overdue_items if block_is_overdue(item))

    if overdue_count > 0:
        suggestions.append(
            {
                "type": "reminder",
                "title": "⚠️ Tareas pendientes",
                "message": f"Tienes {overdue_count} tarea(s) o recordatorio(s) vencido(s)",
                "action": "show_overdue_items",
            }
        )

    # Check if user has no kanban board
    kanban_count = Block.query.filter_by(user_id=current_user.id, type="kanban").count()

    if kanban_count == 0:
        suggestions.append(
            {
                "type": "kanban",
                "title": "📋 Crea tu tablero Kanban",
                "message": "Organiza tus tareas visualmente con un sistema tipo Trello",
                "action": "create_kanban_block",
            }
        )

    # Check if user has no notes
    notes_count = Block.query.filter_by(user_id=current_user.id, type="nota").count()

    if notes_count == 0:
        suggestions.append(
            {
                "type": "note",
                "title": "📝 Bitácora inteligente",
                "message": "Comienza tu bitácora de estudio con notas tipo Notion",
                "action": "create_nota_block",
            }
        )

    # Suggest creating blocks for organization
    total_blocks = Block.query.filter_by(user_id=current_user.id).count()

    if total_blocks >= 5:
        block_count = Block.query.filter_by(
            user_id=current_user.id, type="bloque"
        ).count()

        if block_count == 0:
            suggestions.append(
                {
                    "type": "organization",
                    "title": "🗂️ Organiza con bloques",
                    "message": "Agrupa tus elementos por materias o proyectos",
                    "action": "create_bloque_block",
                }
            )

    return suggestions


def get_default_icon(block_type):
    """Get default icon for block type"""
    icons = {
        "nota": "bi-journal-text",
        "lista": "bi-check2-square",
        "meta": "bi-target",
        "recordatorio": "bi-alarm",
        "frase": "bi-quote",
        "enlace": "bi-link-45deg",
        "tarea": "bi-clipboard-check",
        "kanban": "bi-kanban",
        "objetivo": "bi-trophy",
        "bloque": "bi-grid-3x3",
    }
    return icons.get(block_type, "bi-card-text")


def block_is_overdue(block):
    """Check if a Block with due date metadata is overdue"""
    meta = block.get_metadata()
    due_date_str = meta.get("due_date") or meta.get("deadline")
    if not due_date_str:
        return False
    try:
        due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
        return due_date < datetime.utcnow()
    except (ValueError, TypeError):
        return False


@personal_space_bp.route("/objetivo/nuevo", methods=["GET", "POST"])
@login_required
@activated_required
def create_goal():
    """Form to create a new goal block"""
    if request.method == "POST":
        max_order = (
            db.session.query(db.func.max(Block.order_index))
            .filter_by(user_id=current_user.id)
            .scalar()
            or 0
        )

        block = Block(
            user_id=current_user.id,
            type="objetivo",
            title=request.form.get("title", "Objetivo"),
            content=request.form.get("content", ""),
            order_index=max_order + 1,
        )
        block.set_metadata(
            {
                "color": "indigo",
                "icon": get_default_icon("objetivo"),
                "status": "no_iniciada",
                "progress": 0,
                "deadline": request.form.get("deadline", ""),
                "frequency": "una_vez",
                "category": "academica",
            }
        )

        db.session.add(block)
        db.session.commit()
        flash("Objetivo creado", "success")
        return redirect(url_for("personal_space.index"))

    return render_template("personal_space/forms/create_goal.html")


@personal_space_bp.route("/kanban/nuevo", methods=["GET", "POST"])
@login_required
@activated_required
def create_kanban():
    """Form to create a new kanban block"""
    if request.method == "POST":
        max_order = (
            db.session.query(db.func.max(Block.order_index))
            .filter_by(user_id=current_user.id)
            .scalar()
            or 0
        )

        block = Block(
            user_id=current_user.id,
            type="kanban",
            title=request.form.get("title", "Mi Tablero"),
            content="",
            order_index=max_order + 1,
        )
        block.set_metadata(
            {
                "color": "indigo",
                "icon": get_default_icon("kanban"),
                "columns": {"Por hacer": [], "En curso": [], "Hecho": []},
            }
        )

        db.session.add(block)
        db.session.commit()
        flash("Tablero creado", "success")
        return redirect(url_for("personal_space.index"))

    return render_template("personal_space/forms/create_kanban.html")
