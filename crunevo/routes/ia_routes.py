from flask import Blueprint, render_template, request, jsonify, current_app
import requests

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
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return jsonify({"answer": answer})
    except Exception:
        current_app.logger.exception("AI request failed")
        return jsonify({"error": "api"}), 500


@ia_bp.route("/save", methods=["POST"])
@activated_required
def ia_save():
    """Placeholder endpoint to save a conversation snippet."""
    request.get_json()
    return jsonify({"status": "success"})
