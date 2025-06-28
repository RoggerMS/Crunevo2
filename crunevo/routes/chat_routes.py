
from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash
from flask_login import current_user, login_required
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Message, User, ChatRoom
from crunevo.utils import send_notification
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
@activated_required
def chat_index():
    """Chat global principal"""
    # Obtener mensajes del chat global (últimos 50)
    global_messages = Message.query.filter_by(
        is_global=True, 
        is_deleted=False
    ).order_by(Message.timestamp.desc()).limit(50).all()
    
    # Invertir para mostrar cronológicamente
    global_messages.reverse()
    
    # Obtener usuarios activos (que han enviado mensajes en las últimas 24h)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    active_users = User.query.join(Message).filter(
        Message.timestamp >= recent_cutoff,
        User.id != current_user.id,
        User.activated == True
    ).distinct().limit(20).all()
    
    return render_template("chat/global.html", 
                         messages=global_messages, 
                         active_users=active_users)


@chat_bp.route("/privado")
@activated_required
def private_chats():
    """Lista de conversaciones privadas"""
    # Obtener conversaciones del usuario actual
    conversations = db.session.query(Message).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        ),
        Message.is_global == False,
        Message.is_deleted == False
    ).order_by(Message.timestamp.desc()).all()
    
    # Agrupar por conversación
    chat_partners = {}
    for msg in conversations:
        partner_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        if partner_id and partner_id not in chat_partners:
            partner = User.query.get(partner_id)
            if partner:
                chat_partners[partner_id] = {
                    'user': partner,
                    'last_message': msg,
                    'unread_count': Message.query.filter_by(
                        sender_id=partner_id,
                        receiver_id=current_user.id,
                        is_read=False,
                        is_deleted=False
                    ).count()
                }
    
    return render_template("chat/private_list.html", conversations=chat_partners.values())


@chat_bp.route("/privado/<int:user_id>")
@activated_required
def private_chat(user_id):
    """Chat privado con un usuario específico"""
    partner = User.query.get_or_404(user_id)
    if partner.id == current_user.id:
        flash("No puedes chatear contigo mismo", "error")
        return redirect(url_for("chat.private_chats"))
    
    # Marcar mensajes como leídos
    Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user.id,
        is_read=False
    ).update({Message.is_read: True})
    db.session.commit()
    
    # Obtener mensajes de la conversación
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        ),
        Message.is_global == False,
        Message.is_deleted == False
    ).order_by(Message.timestamp.asc()).limit(100).all()
    
    return render_template("chat/private_chat.html", 
                         partner=partner, 
                         messages=messages)


@chat_bp.route("/enviar", methods=["POST"])
@activated_required
def send_message():
    """Enviar mensaje (global o privado)"""
    data = request.get_json() or request.form
    content = data.get("content", "").strip()
    receiver_id = data.get("receiver_id")
    is_global = data.get("is_global", False)
    
    if not content:
        return jsonify({"error": "Mensaje vacío"}), 400
    
    if len(content) > 1000:
        return jsonify({"error": "Mensaje muy largo"}), 400
    
    # Crear mensaje
    message = Message(
        sender_id=current_user.id,
        receiver_id=int(receiver_id) if receiver_id else None,
        content=content,
        is_global=bool(is_global)
    )
    
    db.session.add(message)
    db.session.commit()
    
    # Enviar notificación si es mensaje privado
    if not is_global and receiver_id:
        send_notification(
            int(receiver_id),
            f"{current_user.username} te envió un mensaje",
            url_for("chat.private_chat", user_id=current_user.id)
        )
    
    return jsonify({
        "status": "ok", 
        "message": message.to_dict(),
        "timestamp": message.timestamp.strftime("%H:%M")
    })


@chat_bp.route("/mensajes/global")
@activated_required
def get_global_messages():
    """API para obtener mensajes globales recientes"""
    since_id = request.args.get("since_id", 0, type=int)
    
    messages = Message.query.filter(
        Message.is_global == True,
        Message.is_deleted == False,
        Message.id > since_id
    ).order_by(Message.timestamp.asc()).limit(50).all()
    
    return jsonify([msg.to_dict() for msg in messages])


@chat_bp.route("/mensajes/privados/<int:user_id>")
@activated_required
def get_private_messages(user_id):
    """API para obtener mensajes privados con un usuario"""
    since_id = request.args.get("since_id", 0, type=int)
    
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        ),
        Message.is_global == False,
        Message.is_deleted == False,
        Message.id > since_id
    ).order_by(Message.timestamp.asc()).limit(50).all()
    
    return jsonify([msg.to_dict() for msg in messages])


@chat_bp.route("/usuarios/buscar")
@activated_required
def search_users():
    """Buscar usuarios para iniciar chat privado"""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        User.username.ilike(f"%{query}%"),
        User.activated == True,
        User.id != current_user.id
    ).limit(10).all()
    
    return jsonify([{
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url
    } for user in users])
