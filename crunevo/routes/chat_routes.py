from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    url_for,
    redirect,
    flash,
    current_app,
)
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Message, User, UserBlock
from crunevo.utils import send_notification
from sqlalchemy import or_, and_
from crunevo.cache.active_users import mark_online, get_active_ids
from crunevo.utils.content_filter import sanitize_message
from werkzeug.utils import secure_filename
import os
import cloudinary.uploader
from mutagen import File as AudioFile

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
@activated_required
def chat_index():
    """Chat global principal"""
    mark_online(current_user.id)
    # Obtener mensajes del chat global (últimos 50)
    global_messages = (
        Message.query.filter_by(is_global=True, is_deleted=False)
        .order_by(Message.timestamp.desc())
        .limit(50)
        .all()
    )

    # Invertir para mostrar cronológicamente
    global_messages.reverse()

    ids = get_active_ids()
    if current_user.id not in ids:
        ids.append(current_user.id)
    active_users = (
        User.query.filter(User.id.in_(ids), User.activated.is_(True)).limit(20).all()
    )

    return render_template(
        "chat/global.html", messages=global_messages, active_users=active_users
    )


@chat_bp.route("/privado")
@activated_required
def private_chats():
    """Lista de conversaciones privadas"""
    # Obtener conversaciones del usuario actual
    conversations = (
        db.session.query(Message)
        .filter(
            or_(
                Message.sender_id == current_user.id,
                Message.receiver_id == current_user.id,
            ),
            Message.is_global.is_(False),
            Message.is_deleted.is_(False),
        )
        .order_by(Message.timestamp.desc())
        .all()
    )

    # Agrupar por conversación
    chat_partners = {}
    for msg in conversations:
        partner_id = (
            msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        )
        if partner_id and partner_id not in chat_partners:
            partner = User.query.get(partner_id)
            if partner:
                chat_partners[partner_id] = {
                    "user": partner,
                    "last_message": msg,
                    "unread_count": Message.query.filter_by(
                        sender_id=partner_id,
                        receiver_id=current_user.id,
                        is_read=False,
                        is_deleted=False,
                    ).count(),
                }

    return render_template(
        "chat/private_list.html", conversations=chat_partners.values()
    )


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
        sender_id=user_id, receiver_id=current_user.id, is_read=False
    ).update({Message.is_read: True})
    db.session.commit()

    # Obtener mensajes de la conversación
    messages = (
        Message.query.filter(
            or_(
                and_(
                    Message.sender_id == current_user.id, Message.receiver_id == user_id
                ),
                and_(
                    Message.sender_id == user_id, Message.receiver_id == current_user.id
                ),
            ),
            Message.is_global.is_(False),
            Message.is_deleted.is_(False),
        )
        .order_by(Message.timestamp.asc())
        .limit(100)
        .all()
    )

    return render_template("chat/private_chat.html", partner=partner, messages=messages)


@chat_bp.route("/enviar", methods=["POST"])
@activated_required
def send_message():
    """Enviar mensaje (global o privado)"""
    data = request.form
    audio = request.files.get("audio")
    attachment = request.files.get("file")
    content = sanitize_message(data.get("content", "").strip())
    receiver_id = data.get("receiver_id")
    is_global = data.get("is_global", False)

    audio_url = None
    attachment_url = None
    if audio and audio.filename:
        ext = os.path.splitext(audio.filename)[1].lower()
        if ext not in {".mp3", ".ogg"}:
            return jsonify({"error": "Formato de audio no permitido"}), 400
        try:
            info = AudioFile(audio)
            if info and info.info.length > 30:
                return jsonify({"error": "Audio demasiado largo"}), 400
        except Exception:
            pass

        cloud_url = current_app.config.get("CLOUDINARY_URL")
        try:
            if cloud_url:
                res = cloudinary.uploader.upload(audio, resource_type="auto")
                audio_url = res["secure_url"]
            else:
                filename = secure_filename(audio.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                audio.save(filepath)
                audio_url = filepath
        except Exception:
            current_app.logger.exception("Error al subir audio")
            return jsonify({"error": "No se pudo subir el audio"}), 500

        content = audio_url

    if attachment and attachment.filename:
        cloud_url = current_app.config.get("CLOUDINARY_URL")
        try:
            if cloud_url:
                res = cloudinary.uploader.upload(attachment, resource_type="auto")
                attachment_url = res["secure_url"]
            else:
                filename = secure_filename(attachment.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                attachment.save(filepath)
                attachment_url = filepath
        except Exception:
            current_app.logger.exception("Error al subir archivo")
            return jsonify({"error": "No se pudo subir el archivo"}), 500

    if not content and not attachment_url:
        return jsonify({"error": "Mensaje vacío"}), 400

    if len(content) > 1000:
        return jsonify({"error": "Mensaje muy largo"}), 400

    if receiver_id:
        block = UserBlock.query.filter(
            db.or_(
                db.and_(
                    UserBlock.blocker_id == int(receiver_id),
                    UserBlock.blocked_id == current_user.id,
                ),
                db.and_(
                    UserBlock.blocker_id == current_user.id,
                    UserBlock.blocked_id == int(receiver_id),
                ),
            )
        ).first()
        if block:
            return jsonify({"error": "No puedes enviar mensajes a este usuario"}), 403

    # Crear mensaje
    message = Message(
        sender_id=current_user.id,
        receiver_id=int(receiver_id) if receiver_id else None,
        content=content,
        attachment_url=attachment_url,
        is_global=bool(is_global),
    )

    db.session.add(message)
    db.session.commit()
    mark_online(current_user.id)

    # Enviar notificación si es mensaje privado
    if not is_global and receiver_id:
        send_notification(
            int(receiver_id),
            f"{current_user.username} te envió un mensaje",
            url_for("chat.private_chat", user_id=current_user.id),
        )

    msg_dict = message.to_dict()
    msg_dict["sender_avatar"] = current_user.avatar_url
    if audio_url:
        msg_dict["audio_url"] = audio_url
    if attachment_url:
        msg_dict["attachment_url"] = attachment_url
    return jsonify(
        {
            "status": "ok",
            "message": msg_dict,
            "timestamp": message.timestamp.strftime("%H:%M"),
        }
    )


@chat_bp.route("/mensajes/global")
@activated_required
def get_global_messages():
    """API para obtener mensajes globales recientes"""
    since_id = request.args.get("since_id", 0, type=int)

    messages = (
        Message.query.filter(
            Message.is_global.is_(True),
            Message.is_deleted.is_(False),
            Message.id > since_id,
        )
        .order_by(Message.timestamp.asc())
        .limit(50)
        .all()
    )

    def augment(msg):
        data = msg.to_dict()
        data["sender_avatar"] = msg.sender.avatar_url
        if msg.content.endswith((".mp3", ".ogg")):
            data["audio_url"] = msg.content
        if msg.attachment_url:
            data["attachment_url"] = msg.attachment_url
        return data

    return jsonify([augment(m) for m in messages])


@chat_bp.route("/mensajes/privados/<int:user_id>")
@activated_required
def get_private_messages(user_id):
    """API para obtener mensajes privados con un usuario"""
    since_id = request.args.get("since_id", 0, type=int)

    messages = (
        Message.query.filter(
            or_(
                and_(
                    Message.sender_id == current_user.id, Message.receiver_id == user_id
                ),
                and_(
                    Message.sender_id == user_id, Message.receiver_id == current_user.id
                ),
            ),
            Message.is_global.is_(False),
            Message.is_deleted.is_(False),
            Message.id > since_id,
        )
        .order_by(Message.timestamp.asc())
        .limit(50)
        .all()
    )

    def augment(msg):
        data = msg.to_dict()
        data["sender_avatar"] = msg.sender.avatar_url
        if msg.content.endswith((".mp3", ".ogg")):
            data["audio_url"] = msg.content
        if msg.attachment_url:
            data["attachment_url"] = msg.attachment_url
        return data

    return jsonify([augment(m) for m in messages])


@chat_bp.route("/usuarios/buscar")
@activated_required
def search_users():
    """Buscar usuarios para iniciar chat privado"""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    users = (
        User.query.filter(
            User.username.ilike(f"%{query}%"),
            User.activated.is_(True),
            User.id != current_user.id,
        )
        .limit(10)
        .all()
    )

    return jsonify(
        [
            {"id": user.id, "username": user.username, "avatar_url": user.avatar_url}
            for user in users
        ]
    )


@chat_bp.route("/usuarios/activos")
@activated_required
def active_users_api():
    """Return currently active users."""
    ids = get_active_ids()
    if current_user.id not in ids:
        ids.append(current_user.id)
    users = User.query.filter(User.id.in_(ids), User.activated.is_(True)).all()
    return jsonify(
        [
            {
                "id": u.id,
                "username": u.username,
                "avatar_url": u.avatar_url,
                "role": u.role,
            }
            for u in users
        ]
    )


@chat_bp.route("/ping", methods=["POST"])
@activated_required
def ping_active():
    mark_online(current_user.id)
    return "", 204


@chat_bp.route("/@<username>")
@activated_required
def private_chat_username(username):
    user = User.query.filter_by(username=username).first_or_404()
    return redirect(url_for("chat.private_chat", user_id=user.id))
