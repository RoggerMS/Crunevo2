from flask import Blueprint, render_template, request, jsonify, current_app
import openai
from openai import RateLimitError
from crunevo.utils.helpers import activated_required

QUICK_RESPONSES = {
    "¿Cómo funciona CRUNEVO?": "CRUNEVO es una comunidad educativa donde puedes subir apuntes, ganar Crolars, participar en misiones y mucho más. ¡Explora todas sus secciones desde el menú superior!",
    "¿Cómo ganar Crolars?": "Puedes ganar Crolars subiendo apuntes útiles, comentando, ayudando en el foro y completando misiones académicas.",
    "Explícame los clubes académicos": "Los clubes académicos son grupos de estudio y colaboración en los que podrás compartir recursos y participar en eventos.",
    "¿Cómo subir apuntes?": "Dirígete a la sección 'Apuntes' y haz clic en 'Subir apunte' para compartir tus materiales.",
    "¿Qué es CRUNEVO+?": "CRUNEVO+ es la suscripción premium que ofrece beneficios adicionales y contenido exclusivo.",
    "¿Dónde están los cursos?": "Los cursos están disponibles en la sección 'Cursos' del menú superior. Allí encontrarás contenidos en video, PDF o enlaces educativos.",
}

ia_bp = Blueprint("ia", __name__, url_prefix="/ia")


@ia_bp.route("/")
@activated_required
def ia_chat():
    ia_enabled = current_app.config.get("IA_ENABLED") and current_app.config.get(
        "OPENAI_API_KEY"
    )
    return render_template("ia/chat.html", ia_enabled=ia_enabled)


@ia_bp.route("/ask", methods=["POST"])
@activated_required
def ia_ask():
    data = request.get_json() or {}
    prompt = (data.get("message", "") or "").strip()
    if not prompt:
        return jsonify({"error": "empty"}), 400

    ia_enabled = current_app.config.get("IA_ENABLED") and current_app.config.get(
        "OPENAI_API_KEY"
    )
    if not ia_enabled:
        answer = QUICK_RESPONSES.get(
            prompt,
            "Por ahora Crunebot está desactivado. Solo puedes usar las opciones rápidas del menú lateral mientras completamos la configuración.",
        )
        return jsonify({"answer": answer})

    try:
        openai.api_key = current_app.config.get("OPENAI_API_KEY")
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        answer = completion.choices[0].message.content
        return jsonify({"answer": answer})
    except RateLimitError:
        current_app.logger.exception("OpenAI request failed")
        return jsonify({"error": "quota"}), 429
    except Exception:
        current_app.logger.exception("OpenAI request failed")
        return jsonify({"error": "api"}), 500


@ia_bp.route("/save", methods=["POST"])
@activated_required
def ia_save():
    """Placeholder endpoint to save a conversation snippet."""
    request.get_json()
    return jsonify({"status": "success"})
