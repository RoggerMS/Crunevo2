from flask import Blueprint, render_template, request, jsonify, current_app
import openai

from crunevo.utils.helpers import activated_required

ia_bp = Blueprint("ia", __name__, url_prefix="/ia")


@ia_bp.route("/")
@activated_required
def ia_chat():
    return render_template("ia/chat.html")


@ia_bp.route("/ask", methods=["POST"])
@activated_required
def ia_ask():
    data = request.get_json() or {}
    prompt = data.get("message", "")
    if not prompt:
        return jsonify({"error": "empty"}), 400
    try:
        openai.api_key = current_app.config.get("OPENAI_API_KEY")
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        answer = completion.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception:
        current_app.logger.exception("OpenAI request failed")
        return jsonify({"error": "api"}), 500


@ia_bp.route("/save", methods=["POST"])
@activated_required
def ia_save():
    """Placeholder endpoint to save a conversation snippet."""
    request.get_json()
    return jsonify({"status": "success"})
