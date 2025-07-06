
# fmt: off
from flask import Blueprint, render_template, request, jsonify, redirect, url_for  # noqa: F401
# fmt: on
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.personal_block import PersonalBlock
from crunevo.utils.helpers import activated_required
from datetime import datetime
import json  # noqa: F401

personal_space_bp = Blueprint('personal_space', __name__, url_prefix='/espacio-personal')


@personal_space_bp.route('/')
@login_required
@activated_required
def index():
    """Main personal space dashboard"""
    blocks = PersonalBlock.query.filter_by(user_id=current_user.id)\
        .order_by(PersonalBlock.order_position.asc(), PersonalBlock.created_at.desc()).all()
    
    # Get smart suggestions
    suggestions = get_smart_suggestions()
    
    return render_template('personal_space/index.html', 
                         blocks=blocks, 
                         suggestions=suggestions)


@personal_space_bp.route('/api/blocks', methods=['GET'])
@login_required
def get_blocks():
    """API endpoint to get all user blocks"""
    blocks = PersonalBlock.query.filter_by(user_id=current_user.id)\
        .order_by(PersonalBlock.order_position.asc()).all()
    
    return jsonify({
        'success': True,
        'blocks': [block.to_dict() for block in blocks]
    })


@personal_space_bp.route('/api/blocks', methods=['POST'])
@login_required
def create_block():
    """Create a new personal block"""
    data = request.get_json()
    
    if not data or 'block_type' not in data:
        return jsonify({'success': False, 'message': 'Tipo de bloque requerido'}), 400
    
    # Get the highest order position
    max_order = db.session.query(db.func.max(PersonalBlock.order_position))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    block = PersonalBlock(
        user_id=current_user.id,
        block_type=data['block_type'],
        title=data.get('title', ''),
        content=data.get('content', ''),
        order_position=max_order + 1,
        color=data.get('color', 'indigo'),
        icon=data.get('icon', get_default_icon(data['block_type']))
    )
    
    # Set default metadata based on block type
    if data['block_type'] == 'lista':
        block.set_metadata({'tasks': []})
    elif data['block_type'] == 'meta':
        block.set_metadata({'progress': 0, 'target_date': ''})
    elif data['block_type'] == 'recordatorio':
        block.set_metadata({'due_date': '', 'priority': 'medium'})
    elif data['block_type'] == 'frase':
        block.set_metadata({'author': '', 'category': 'motivacional'})
    elif data['block_type'] == 'enlace':
        block.set_metadata({'url': '', 'description': ''})
    
    # Set metadata if provided
    if 'metadata' in data:
        metadata = block.get_metadata()
        metadata.update(data['metadata'])
        block.set_metadata(metadata)
    
    db.session.add(block)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'block': block.to_dict(),
        'message': 'Bloque creado exitosamente'
    })


@personal_space_bp.route('/api/blocks/<int:block_id>', methods=['PUT'])
@login_required
def update_block(block_id):
    """Update an existing block"""
    block = PersonalBlock.query.filter_by(id=block_id, user_id=current_user.id).first()
    
    if not block:
        return jsonify({'success': False, 'message': 'Bloque no encontrado'}), 404
    
    data = request.get_json()
    
    # Update basic fields
    if 'title' in data:
        block.title = data['title']
    if 'content' in data:
        block.content = data['content']
    if 'color' in data:
        block.color = data['color']
    if 'icon' in data:
        block.icon = data['icon']
    if 'is_featured' in data:
        block.is_featured = data['is_featured']
    
    # Update metadata
    if 'metadata' in data:
        metadata = block.get_metadata()
        metadata.update(data['metadata'])
        block.set_metadata(metadata)
    
    block.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'block': block.to_dict(),
        'message': 'Bloque actualizado'
    })


@personal_space_bp.route('/api/blocks/<int:block_id>', methods=['DELETE'])
@login_required
def delete_block(block_id):
    """Delete a block"""
    block = PersonalBlock.query.filter_by(id=block_id, user_id=current_user.id).first()
    
    if not block:
        return jsonify({'success': False, 'message': 'Bloque no encontrado'}), 404
    
    db.session.delete(block)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Bloque eliminado'
    })


@personal_space_bp.route('/api/blocks/reorder', methods=['POST'])
@login_required
def reorder_blocks():
    """Update block order positions"""
    data = request.get_json()
    block_orders = data.get('blocks', [])
    
    for item in block_orders:
        block = PersonalBlock.query.filter_by(
            id=item['id'], 
            user_id=current_user.id
        ).first()
        
        if block:
            block.order_position = item['position']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Orden actualizado'
    })


@personal_space_bp.route('/api/suggestions')
@login_required
def api_suggestions():
    """Get smart suggestions for the user"""
    suggestions = get_smart_suggestions()
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })


def get_smart_suggestions():
    """Generate smart suggestions based on user activity"""
    suggestions = []
    
    # Check if user has any goals this week
    recent_goals = PersonalBlock.query.filter_by(
        user_id=current_user.id, 
        block_type='meta'
    ).filter(
        PersonalBlock.created_at >= datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    ).count()
    
    if recent_goals == 0:
        suggestions.append({
            'type': 'goal',
            'title': '🎯 Establece una meta',
            'message': 'Aún no has establecido metas esta semana. ¡Define un objetivo académico!',
            'action': 'create_goal_block'
        })
    
    # Check for overdue reminders
    overdue_reminders = PersonalBlock.query.filter_by(
        user_id=current_user.id,
        block_type='recordatorio'
    ).all()
    
    overdue_count = sum(1 for reminder in overdue_reminders if reminder.is_overdue())
    
    if overdue_count > 0:
        suggestions.append({
            'type': 'reminder',
            'title': '⏰ Recordatorios pendientes',
            'message': f'Tienes {overdue_count} recordatorio(s) vencido(s). ¡Revísalos!',
            'action': 'show_overdue_reminders'
        })
    
    # Check if user has no notes
    notes_count = PersonalBlock.query.filter_by(
        user_id=current_user.id,
        block_type='nota'
    ).count()
    
    if notes_count == 0:
        suggestions.append({
            'type': 'note',
            'title': '📝 Crea tu primera nota',
            'message': 'Organiza tus ideas y pensamientos con notas rápidas',
            'action': 'create_note_block'
        })
    
    return suggestions


def get_default_icon(block_type):
    """Get default icon for block type"""
    icons = {
        'nota': 'bi-journal-text',
        'lista': 'bi-check2-square',
        'meta': 'bi-target',
        'recordatorio': 'bi-alarm',
        'frase': 'bi-quote',
        'enlace': 'bi-link-45deg'
    }
    return icons.get(block_type, 'bi-card-text')
