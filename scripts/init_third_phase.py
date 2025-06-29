#!/usr/bin/env python3
"""
Script para inicializar datos de ejemplo para la tercera fase de funcionalidades
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path to import crunevo modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models.event import Event
from crunevo.models.forum import ForumQuestion, ForumAnswer
from crunevo.models.user import User


def init_sample_events():
    """Initialize sample events"""
    events_data = [
        {
            "title": "Día del Apunte - Concurso Especial",
            "description": "Participa en nuestro concurso mensual subiendo tus mejores apuntes. Los ganadores recibirán Crolars extra y reconocimiento.",
            "event_date": datetime.now() + timedelta(days=15),
            "category": "Académico",
            "is_featured": True,
            "rewards": "Ganadores reciben 50 Crolars extra + certificado especial",
        },
        {
            "title": "Mesa Redonda: Futuro de la Educación en Perú",
            "description": "Debate abierto sobre los retos y oportunidades en el sistema educativo peruano. Participación de estudiantes de todas las carreras.",
            "event_date": datetime.now() + timedelta(days=7),
            "category": "Debate",
            "is_featured": False,
            "rewards": "10 Crolars por participación activa",
        },
        {
            "title": "Hackathon Educativo CRUNEVO",
            "description": "Desarrolla soluciones tecnológicas para problemas educativos. Equipos multidisciplinarios de estudiantes.",
            "event_date": datetime.now() + timedelta(days=30),
            "category": "Tecnología",
            "is_featured": True,
            "rewards": "Premios en Crolars: 1er lugar 200, 2do 100, 3er 50",
        },
    ]

    for event_data in events_data:
        existing = Event.query.filter_by(title=event_data["title"]).first()
        if not existing:
            event = Event(**event_data)
            db.session.add(event)

    db.session.commit()
    print("✅ Eventos de ejemplo creados")


def init_sample_forum_content():
    """Initialize sample forum questions"""
    # Get a sample user (first user)
    sample_user = User.query.first()
    if not sample_user:
        print("❌ No hay usuarios para crear contenido de ejemplo")
        return

    questions_data = [
        {
            "title": "¿Cómo estudiar efectivamente para exámenes de matemáticas?",
            "content": "Tengo dificultades para organizar mi tiempo de estudio en matemáticas. ¿Qué técnicas me recomiendan para preparar exámenes de cálculo y álgebra?",
            "category": "Matemáticas",
            "author_id": sample_user.id,
        },
        {
            "title": "Mejores recursos para aprender programación desde cero",
            "content": "Soy nuevo en programación y quiero empezar con Python. ¿Conocen buenos recursos gratuitos o plataformas que recomienden?",
            "category": "Tecnología",
            "author_id": sample_user.id,
        },
        {
            "title": "Técnicas de redacción académica para ensayos universitarios",
            "content": "Necesito mejorar mi escritura académica. ¿Qué estructura recomiendan para ensayos argumentativos y cómo citar correctamente las fuentes?",
            "category": "Lenguas",
            "author_id": sample_user.id,
        },
    ]

    for question_data in questions_data:
        existing = ForumQuestion.query.filter_by(title=question_data["title"]).first()
        if not existing:
            question = ForumQuestion(**question_data)
            db.session.add(question)
            db.session.flush()  # To get the ID

            # Add a sample answer
            answer = ForumAnswer(
                content="Excelente pregunta. Te recomiendo empezar creando un plan de estudio estructurado y usar la técnica Pomodoro para mantener la concentración. También revisa los apuntes disponibles en CRUNEVO para tu área de estudio.",
                question_id=question.id,
                author_id=sample_user.id,
                votes=5,
            )
            db.session.add(answer)

    db.session.commit()
    print("✅ Contenido del foro creado")


def main():
    app = create_app()
    with app.app_context():
        print("🚀 Inicializando datos de la tercera fase...")

        init_sample_events()
        init_sample_forum_content()

        print("✅ Inicialización completada")


if __name__ == "__main__":
    main()
