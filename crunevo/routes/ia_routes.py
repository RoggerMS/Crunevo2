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
        resp = requests.post(
            "https://openrouter.ai/deepseek/deepseek-chat-v3-0324:free/api",
            json={
                "model": "deepseek/deepseek-chat:free",
                "api_key": "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",
                "prompt": prompt,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = (
            data.get("answer")
            or data.get("choices", [{}])[0].get("message", {}).get("content")
            or ""
        )
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
