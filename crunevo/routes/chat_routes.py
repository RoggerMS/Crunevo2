from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import current_user
from crunevo.utils.helpers import activated_required
from crunevo.extensions import db
from crunevo.models import Message, User
from crunevo.utils import send_notification

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/")
@activated_required
def chat_index():
    users = User.query.all()
    return render_template("chat/chat.html", users=users)


@chat_bp.route("/send", methods=["POST"])
@activated_required
def send_message():
    receiver_id = request.form["receiver_id"]
    content = request.form["content"]
    msg = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()
    send_notification(
        receiver_id,
        f"{current_user.username} te envió un mensaje",
        url_for("chat.chat_index"),
    )
    return jsonify({"status": "ok", "timestamp": msg.timestamp.strftime("%H:%M")})
