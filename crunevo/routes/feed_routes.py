from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from crunevo.models import Note

feed_bp = Blueprint('feed', __name__)


@feed_bp.route('/')
@login_required
def index():
    notes = Note.query.order_by(Note.created_at.desc()).limit(20).all()
    return render_template('feed/feed.html', notes=notes)


@feed_bp.route('/trending')
@login_required
def trending():
    notes = Note.query.order_by(Note.views.desc()).limit(10).all()
    return render_template('feed/feed.html', notes=notes, trending=True)


@feed_bp.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    question = request.json.get('question')
    # placeholder for future AI integration
    return jsonify({'answer': f'Respuesta a "{question}"'})


@feed_bp.route('/api/analizar', methods=['POST'])
@login_required
def api_analizar():
    text = request.json.get('text')
    return jsonify({'analysis': f'Analisis simple de {len(text)} caracteres'})
