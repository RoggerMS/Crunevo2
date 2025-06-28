from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
import json
import re

crunebot_bp = Blueprint("crunebot", __name__)

# Crunebot knowledge base
CRUNEBOT_RESPONSES = {
    "que_es_crunevo": {
        "keywords": [
            "qué es crunevo",
            "que es crunevo",
            "crunevo",
            "plataforma",
            "explicar",
        ],
        "response": "¡Hola! 🎓 CRUNEVO es la red educativa peruana hecha por estudiantes, para estudiantes. Aquí puedes compartir apuntes, hacer preguntas en el foro, unirte a clubes académicos, participar en eventos y ganar Crolars (nuestra moneda virtual). ¡Es tu comunidad universitaria digital!",
    },
    "como_ganar_crolars": {
        "keywords": [
            "cómo ganar crolars",
            "como ganar crolars",
            "crolars",
            "ganar dinero",
            "moneda",
            "créditos",
        ],
        "response": "💰 Puedes ganar Crolars de varias formas:\n• Subir apuntes de calidad (+5 Crolars)\n• Completar misiones (+2-10 Crolars)\n• Participar en el foro (+3-5 Crolars)\n• Unirte a clubes (+2 Crolars)\n• Participar en eventos (+3 Crolars)\n• Mantener rachas de login (+2-10 Crolars)\n¡Los Crolars se pueden usar en nuestra tienda!",
    },
    "donde_clubes": {
        "keywords": [
            "dónde están los clubes",
            "donde estan los clubes",
            "clubes",
            "unirme club",
            "encontrar club",
        ],
        "response": "👥 Los clubes están en la sección 'Clubes' del menú principal. Allí encontrarás clubes por carrera como Matemáticas, Educación, Informática, etc. ¡Únete a los que más te interesen para conectar con estudiantes de tu área!",
    },
    "ganar_dinero": {
        "keywords": [
            "puedo ganar dinero",
            "dinero real",
            "monetizar",
            "pagar",
            "cobrar",
        ],
        "response": "💡 CRUNEVO es una plataforma educativa gratuita. Los Crolars son una moneda virtual para intercambiar dentro de la plataforma, no dinero real. Nuestro objetivo es fomentar el aprendizaje colaborativo y la ayuda mutua entre estudiantes peruanos. ¡El conocimiento es la mejor recompensa!",
    },
    "como_subir_apuntes": {
        "keywords": [
            "cómo subir apuntes",
            "como subir apuntes",
            "subir notas",
            "cargar archivos",
            "apuntes",
        ],
        "response": "📚 Para subir apuntes:\n1. Ve a la sección 'Apuntes'\n2. Haz clic en 'Subir Apunte'\n3. Completa el título, descripción y etiquetas\n4. Sube tu archivo PDF\n5. ¡Listo! Recibirás Crolars cuando otros descarguen tu contenido.",
    },
    "foro_preguntas": {
        "keywords": [
            "cómo hacer preguntas",
            "como hacer preguntas",
            "foro",
            "preguntar",
            "ayuda académica",
        ],
        "response": "❓ En el Foro puedes:\n• Hacer preguntas académicas\n• Responder dudas de otros\n• Votar las mejores respuestas\n• Ganar Crolars por participar\nVe a 'Foro' → 'Hacer Pregunta' y describe tu duda con detalle. ¡La comunidad te ayudará!",
    },
    "eventos": {
        "keywords": ["eventos", "actividades", "participar eventos", "calendario"],
        "response": "📅 En la sección 'Eventos' encontrarás actividades especiales como:\n• Competencias académicas\n• Talleres educativos\n• Días temáticos (ej: Día del Apunte)\n¡Participa para ganar Crolars extra y conectar con la comunidad!",
    },
    "tienda": {
        "keywords": ["tienda", "comprar", "productos", "canje", "usar crolars"],
        "response": "🛒 En la Tienda puedes canjear tus Crolars por:\n• Productos educativos\n• Acceso premium\n• Materiales de estudio\n• ¡Y más sorpresas!\nRevisa regularmente porque agregamos nuevos productos.",
    },
    "certificados": {
        "keywords": ["certificados", "diplomas", "reconocimientos", "logros"],
        "response": "🏆 Puedes obtener certificados digitales por:\n• Participación activa en CRUNEVO\n• Completar 10 misiones\n• Subir 3 o más apuntes\nVe a tu perfil → 'Certificados' para ver cuáles puedes generar.",
    },
    "ayuda_general": {
        "keywords": ["ayuda", "no entiendo", "confused", "socorro", "help"],
        "response": "🤗 ¡Estoy aquí para ayudarte! Puedes preguntarme sobre:\n• Qué es CRUNEVO\n• Cómo ganar Crolars\n• Dónde encontrar clubes\n• Cómo usar el foro\n• Subir apuntes\n• Eventos y certificados\n¿Sobre qué quieres saber más?",
    },
}


def find_best_response(user_message):
    """Find the best response based on keywords"""
    user_message = user_message.lower().strip()

    best_match = None
    max_score = 0

    for response_key, data in CRUNEBOT_RESPONSES.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in user_message:
                score += len(keyword)  # Longer matches get higher score

        if score > max_score:
            max_score = score
            best_match = data["response"]

    if best_match:
        return best_match

    # Default response
    return "🤔 Interesante pregunta. Te recomiendo:\n• Explorar el foro para dudas académicas\n• Revisar los clubes de tu carrera\n• Subir apuntes para ganar Crolars\n• Participar en eventos\n\n¿Hay algo específico en lo que pueda ayudarte?"


@crunebot_bp.route("/crunebot")
def crunebot_chat():
    """Crunebot chat interface"""
    return render_template("crunebot/chat.html")


@crunebot_bp.route("/api/crunebot/message", methods=["POST"])
def crunebot_message():
    """Process message and return Crunebot response"""
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify(
            {
                "response": "¡Hola! Soy Crunebot, tu guía en CRUNEVO. ¿En qué puedo ayudarte hoy? 😊"
            }
        )

    # Get response
    response = find_best_response(user_message)

    return jsonify(
        {
            "response": response,
            "timestamp": "2024-01-01T00:00:00Z",  # You can use actual timestamp
        }
    )
