from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Message, User

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/')
@login_required
def chat_index():
    users = User.query.all()
    return render_template('chat/chat.html', users=users)


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form['receiver_id']
    content = request.form['content']
    msg = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'status': 'ok'})
