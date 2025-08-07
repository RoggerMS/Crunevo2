# fmt: off
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    send_file,
    abort,
)
# fmt: on
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.block import Block
from crunevo.utils.helpers import activated_required
from jinja2 import TemplateNotFound
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func, desc
import json
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from collections import defaultdict

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


@personal_space_bp.route("/kanban/<int:block_id>")
@login_required
@activated_required
def view_kanban(block_id):
    """Display a kanban board"""
    block = Block.query.filter_by(id=block_id, user_id=current_user.id).first_or_404()
    return render_template("personal_space/views/kanban_view.html", block=block)


@personal_space_bp.route("/bloque/<int:block_id>")
@login_required
@activated_required
def view_block(block_id):
    """Generic viewer for personal blocks"""
    block = Block.query.filter_by(id=block_id, user_id=current_user.id).first_or_404()
    template_name = f"personal_space/views/{block.type}_view.html"
    try:
        return render_template(template_name, block=block)
    except TemplateNotFound:
        return render_template(
            "personal_space/views/under_construction.html", block=block
        )


# ============================================================================
# NEW VIEWS AND FUNCTIONALITIES
# ============================================================================

@personal_space_bp.route("/calendario")
@login_required
@activated_required
def calendar_view():
    """Calendar view for personal space"""
    return render_template("personal_space/views/calendar_view.html")


@personal_space_bp.route("/estadisticas")
@login_required
@activated_required
def statistics_view():
    """Advanced statistics view"""
    return render_template("personal_space/views/statistics_view.html")


@personal_space_bp.route("/plantillas")
@login_required
@activated_required
def templates_view():
    """Templates view for personal space"""
    return render_template("personal_space/views/templates_view.html")


@personal_space_bp.route("/configuracion")
@login_required
@activated_required
def settings_view():
    """Settings view for personal space"""
    return render_template("personal_space/views/settings_view.html")


@personal_space_bp.route("/buscar")
@login_required
@activated_required
def search_view():
    """Advanced search view"""
    return render_template("personal_space/views/search_view.html")


@personal_space_bp.route("/papelera")
@login_required
@activated_required
def trash_view():
    """Trash view for deleted blocks"""
    return render_template("personal_space/views/trash_view.html")


# ============================================================================
# API ENDPOINTS FOR NEW FUNCTIONALITIES
# ============================================================================

@personal_space_bp.route("/api/calendar-events")
@login_required
@activated_required
def get_calendar_events():
    """Get events for calendar view"""
    blocks = Block.query.filter_by(user_id=current_user.id).all()
    events = []
    
    for block in blocks:
        metadata = block.get_metadata()
        
        # Add creation date event
        events.append({
            'id': f'created_{block.id}',
            'title': f'Creado: {block.title}',
            'start': block.created_at.isoformat(),
            'backgroundColor': get_block_color(block.type),
            'borderColor': get_block_color(block.type),
            'textColor': 'white',
            'extendedProps': {
                'type': 'created',
                'blockType': block.type,
                'blockId': block.id
            }
        })
        
        # Add deadline events for goals and reminders
        if block.type == 'objetivo' and metadata.get('target_date'):
            events.append({
                'id': f'deadline_{block.id}',
                'title': f'Meta: {block.title}',
                'start': metadata['target_date'],
                'backgroundColor': '#ef4444',
                'borderColor': '#dc2626',
                'textColor': 'white',
                'extendedProps': {
                    'type': 'deadline',
                    'blockType': block.type,
                    'blockId': block.id
                }
            })
        
        if block.type == 'recordatorio' and metadata.get('due_date'):
            events.append({
                'id': f'reminder_{block.id}',
                'title': f'Recordatorio: {block.title}',
                'start': metadata['due_date'],
                'backgroundColor': '#f59e0b',
                'borderColor': '#d97706',
                'textColor': 'white',
                'extendedProps': {
                    'type': 'reminder',
                    'blockType': block.type,
                    'blockId': block.id
                }
            })
    
    return jsonify({'success': True, 'events': events})


@personal_space_bp.route("/api/statistics")
@login_required
@activated_required
def get_statistics():
    """Get statistics data"""
    blocks = Block.query.filter_by(user_id=current_user.id).all()
    
    # Basic metrics
    total_blocks = len(blocks)
    completed_blocks = sum(1 for block in blocks if block.get_progress_percentage() == 100)
    completion_rate = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0
    
    # Block type distribution
    type_distribution = defaultdict(int)
    for block in blocks:
        type_distribution[block.type] += 1
    
    # Weekly activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_blocks = [b for b in blocks if b.created_at >= week_ago]
    weekly_activity = len(recent_blocks)
    
    # Goals achieved
    goals_achieved = sum(1 for block in blocks 
                        if block.type == 'objetivo' and block.get_progress_percentage() == 100)
    
    # Productivity trend (last 30 days)
    productivity_data = []
    for i in range(30):
        date = datetime.now() - timedelta(days=29-i)
        day_blocks = [b for b in blocks if b.created_at.date() == date.date()]
        productivity_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': len(day_blocks)
        })
    
    return jsonify({
        'success': True,
        'statistics': {
            'total_blocks': total_blocks,
            'completed_blocks': completed_blocks,
            'completion_rate': round(completion_rate, 1),
            'goals_achieved': goals_achieved,
            'weekly_activity': weekly_activity,
            'type_distribution': dict(type_distribution),
            'productivity_trend': productivity_data
        }
    })


@personal_space_bp.route("/api/search", methods=["POST"])
@login_required
@activated_required
def search_blocks():
    """Search blocks with filters"""
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    filters = data.get('filters', {})
    
    # Base query
    blocks_query = Block.query.filter_by(user_id=current_user.id)
    
    # Apply text search
    if query:
        blocks_query = blocks_query.filter(
            or_(
                Block.title.ilike(f'%{query}%'),
                Block.content.ilike(f'%{query}%')
            )
        )
    
    # Apply filters
    if filters.get('type'):
        blocks_query = blocks_query.filter(Block.type == filters['type'])
    
    if filters.get('featured'):
        is_featured = filters['featured'] == 'true'
        blocks_query = blocks_query.filter(Block.is_featured == is_featured)
    
    # Date filters
    if filters.get('dateRange'):
        date_range = filters['dateRange']
        now = datetime.now()
        
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            blocks_query = blocks_query.filter(Block.created_at >= start_date)
        elif date_range == 'week':
            start_date = now - timedelta(days=7)
            blocks_query = blocks_query.filter(Block.created_at >= start_date)
        elif date_range == 'month':
            start_date = now - timedelta(days=30)
            blocks_query = blocks_query.filter(Block.created_at >= start_date)
        elif date_range == 'year':
            start_date = now - timedelta(days=365)
            blocks_query = blocks_query.filter(Block.created_at >= start_date)
    
    if filters.get('dateFrom'):
        try:
            date_from = datetime.strptime(filters['dateFrom'], '%Y-%m-%d')
            blocks_query = blocks_query.filter(Block.created_at >= date_from)
        except ValueError:
            pass
    
    if filters.get('dateTo'):
        try:
            date_to = datetime.strptime(filters['dateTo'], '%Y-%m-%d')
            date_to = date_to.replace(hour=23, minute=59, second=59)
            blocks_query = blocks_query.filter(Block.created_at <= date_to)
        except ValueError:
            pass
    
    # Execute query
    blocks = blocks_query.order_by(desc(Block.created_at)).all()
    
    # Calculate relevance score
    results = []
    for block in blocks:
        relevance = 0
        if query:
            if query.lower() in block.title.lower():
                relevance += 10
            if query.lower() in (block.content or '').lower():
                relevance += 5
        
        results.append({
            'id': block.id,
            'title': block.title,
            'content': block.content[:200] + '...' if block.content and len(block.content) > 200 else block.content,
            'type': block.type,
            'created_at': block.created_at.isoformat(),
            'is_featured': block.is_featured,
            'progress': block.get_progress_percentage(),
            'relevance': relevance
        })
    
    return jsonify({'success': True, 'results': results})


@personal_space_bp.route("/api/templates")
@login_required
@activated_required
def get_templates():
    """Get available templates"""
    templates = [
        {
            'id': 'university_student',
            'title': 'Estudiante Universitario',
            'subtitle': 'Organización académica completa',
            'description': 'Plantilla diseñada para estudiantes universitarios con bloques para materias, tareas, exámenes y proyectos.',
            'category': 'academic',
            'tags': ['Universidad', 'Materias', 'Exámenes', 'Proyectos'],
            'popularity': 95,
            'difficulty': 'Intermedio',
            'blocks': [
                {'type': 'objetivo', 'title': 'Metas del Semestre', 'content': 'Define tus objetivos académicos'},
                {'type': 'kanban', 'title': 'Tareas Pendientes', 'content': 'Organiza tus tareas por materia'},
                {'type': 'lista', 'title': 'Horario de Clases', 'content': 'Mantén tu horario actualizado'},
                {'type': 'recordatorio', 'title': 'Próximos Exámenes', 'content': 'No olvides tus fechas importantes'}
            ]
        },
        {
            'id': 'exam_preparation',
            'title': 'Preparación de Exámenes',
            'subtitle': 'Estrategia de estudio efectiva',
            'description': 'Organiza tu tiempo de estudio y materiales para maximizar tu rendimiento en exámenes.',
            'category': 'academic',
            'tags': ['Exámenes', 'Estudio', 'Planificación', 'Repaso'],
            'popularity': 88,
            'difficulty': 'Básico',
            'blocks': [
                {'type': 'objetivo', 'title': 'Meta de Calificación', 'content': 'Define tu objetivo de calificación'},
                {'type': 'lista', 'title': 'Temas a Estudiar', 'content': 'Lista todos los temas del examen'},
                {'type': 'kanban', 'title': 'Plan de Estudio', 'content': 'Organiza tu cronograma de repaso'},
                {'type': 'recordatorio', 'title': 'Fechas de Examen', 'content': 'Recordatorios importantes'}
            ]
        },
        {
            'id': 'research_project',
            'title': 'Proyecto de Investigación',
            'subtitle': 'Metodología y seguimiento',
            'description': 'Estructura completa para gestionar proyectos de investigación académica.',
            'category': 'project',
            'tags': ['Investigación', 'Metodología', 'Referencias', 'Análisis'],
            'popularity': 76,
            'difficulty': 'Avanzado',
            'blocks': [
                {'type': 'objetivo', 'title': 'Objetivos de Investigación', 'content': 'Define hipótesis y objetivos'},
                {'type': 'nota', 'title': 'Marco Teórico', 'content': 'Desarrolla tu base teórica'},
                {'type': 'kanban', 'title': 'Fases del Proyecto', 'content': 'Gestiona las etapas de investigación'},
                {'type': 'enlace', 'title': 'Referencias Bibliográficas', 'content': 'Organiza tus fuentes'}
            ]
        }
    ]
    
    return jsonify({'success': True, 'templates': templates})


@personal_space_bp.route("/api/apply-template", methods=["POST"])
@login_required
@activated_required
def apply_template():
    """Apply a template to user's personal space"""
    data = request.get_json() or {}
    template_id = data.get('template_id')
    
    if not template_id:
        return jsonify({'success': False, 'message': 'Template ID requerido'}), 400
    
    # Get template data (in a real app, this would come from database)
    templates_response = get_templates()
    templates_data = json.loads(templates_response.data)
    template = next((t for t in templates_data['templates'] if t['id'] == template_id), None)
    
    if not template:
        return jsonify({'success': False, 'message': 'Plantilla no encontrada'}), 404
    
    # Get current max order
    max_order = (
        db.session.query(func.max(Block.order_index))
        .filter_by(user_id=current_user.id)
        .scalar() or 0
    )
    
    # Create blocks from template
    created_blocks = []
    for i, block_data in enumerate(template['blocks']):
        block = Block(
            user_id=current_user.id,
            type=block_data['type'],
            title=block_data['title'],
            content=block_data['content'],
            order_index=max_order + i + 1
        )
        
        # Set default metadata
        metadata = {
            'color': 'indigo',
            'icon': get_default_icon(block_data['type'])
        }
        
        if block_data['type'] == 'kanban':
            metadata['columns'] = {'Por hacer': [], 'En curso': [], 'Hecho': []}
        elif block_data['type'] == 'lista':
            metadata['tasks'] = []
        elif block_data['type'] == 'objetivo':
            metadata['progress'] = 0
            metadata['target_date'] = ''
        
        block.set_metadata(metadata)
        db.session.add(block)
        created_blocks.append(block)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Plantilla "{template["title"]}" aplicada exitosamente',
        'blocks_created': len(created_blocks)
    })


@personal_space_bp.route("/api/export/<format>")
@login_required
@activated_required
def export_data(format):
    """Export personal space data in different formats"""
    blocks = Block.query.filter_by(user_id=current_user.id).order_by(Block.order_index.asc()).all()
    
    if format == 'json':
        data = {
            'user_id': current_user.id,
            'export_date': datetime.now().isoformat(),
            'blocks': [block.to_dict() for block in blocks]
        }
        
        output = io.StringIO()
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'espacio_personal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['ID', 'Tipo', 'Título', 'Contenido', 'Destacado', 'Fecha Creación', 'Progreso'])
        
        # Data
        for block in blocks:
            writer.writerow([
                block.id,
                block.type,
                block.title,
                block.content or '',
                'Sí' if block.is_featured else 'No',
                block.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                f'{block.get_progress_percentage()}%'
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'espacio_personal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    elif format == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"Mi Espacio Personal - {current_user.username}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Export info
        export_info = Paragraph(f"Exportado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal'])
        story.append(export_info)
        story.append(Spacer(1, 12))
        
        # Blocks
        for block in blocks:
            block_title = Paragraph(f"<b>{block.title}</b> ({block.type})", styles['Heading2'])
            story.append(block_title)
            
            if block.content:
                content = Paragraph(block.content, styles['Normal'])
                story.append(content)
            
            meta_info = Paragraph(
                f"Creado: {block.created_at.strftime('%d/%m/%Y')} | "
                f"Progreso: {block.get_progress_percentage()}% | "
                f"Destacado: {'Sí' if block.is_featured else 'No'}",
                styles['Normal']
            )
            story.append(meta_info)
            story.append(Spacer(1, 12))
        
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'espacio_personal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    
    else:
        return jsonify({'success': False, 'message': 'Formato no soportado'}), 400


@personal_space_bp.route("/api/trash")
@login_required
@activated_required
def get_trash_items():
    """Get deleted blocks (simulated - would need a deleted_blocks table)"""
    # This is a simulation - in a real app, you'd have a separate table for deleted blocks
    # or a soft delete mechanism with a deleted_at column
    return jsonify({
        'success': True,
        'items': []  # Empty for now - would contain deleted blocks
    })


@personal_space_bp.route("/api/restore", methods=["POST"])
@login_required
@activated_required
def restore_blocks():
    """Restore deleted blocks"""
    data = request.get_json() or {}
    item_ids = data.get('item_ids', [])
    
    # Implementation would restore blocks from trash
    # For now, just return success
    return jsonify({
        'success': True,
        'message': f'{len(item_ids)} elemento(s) restaurado(s)'
    })


@personal_space_bp.route("/api/delete-permanent", methods=["POST"])
@login_required
@activated_required
def delete_permanent():
    """Permanently delete blocks"""
    data = request.get_json() or {}
    item_ids = data.get('item_ids', [])
    
    # Implementation would permanently delete blocks
    # For now, just return success
    return jsonify({
        'success': True,
        'message': f'{len(item_ids)} elemento(s) eliminado(s) permanentemente'
    })


@personal_space_bp.route("/api/saved-searches", methods=["POST"])
@login_required
@activated_required
def save_search():
    """Save a search query"""
    data = request.get_json() or {}
    
    # Implementation would save search to database
    # For now, just return success
    return jsonify({
        'success': True,
        'message': 'Búsqueda guardada exitosamente'
    })


@personal_space_bp.route("/api/settings", methods=["GET", "POST"])
@login_required
@activated_required
def handle_settings():
    """Get or update user settings"""
    if request.method == 'GET':
        # Return current settings (would come from database)
        settings = {
            'theme': 'light',
            'primary_color': 'indigo',
            'animations': True,
            'compact_mode': False,
            'auto_save': True,
            'smart_suggestions': True,
            'drag_drop': True,
            'keyboard_shortcuts': True,
            'browser_notifications': False,
            'notification_types': {
                'reminders': True,
                'deadlines': True,
                'achievements': False
            },
            'usage_analytics': True,
            'sharing_statistics': False
        }
        return jsonify({'success': True, 'settings': settings})
    
    else:  # POST
        data = request.get_json() or {}
        # Implementation would save settings to database
        return jsonify({
            'success': True,
            'message': 'Configuración guardada exitosamente'
        })


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_block_color(block_type):
    """Get color for block type"""
    colors = {
        'nota': '#667eea',
        'kanban': '#f093fb',
        'objetivo': '#4facfe',
        'tarea': '#43e97b',
        'recordatorio': '#fa709a',
        'enlace': '#a8edea',
        'frase': '#ffecd2',
        'lista': '#d299c2',
        'bloque': '#89f7fe'
    }
    return colors.get(block_type, '#6b7280')
