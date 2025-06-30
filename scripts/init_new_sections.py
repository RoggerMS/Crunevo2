#!/usr/bin/env python3
"""
Script para inicializar datos de ejemplo para las nuevas secciones de Crunevo
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path to import crunevo modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models.club import Club
from crunevo.models.forum import ForumQuestion
from crunevo.models.event import Event
from crunevo.models.user import User


def init_clubs():
    """Initialize sample clubs"""
    clubs_data = [
        {
            "name": "Club de Matemáticas",
            "career": "Matemáticas",
            "description": "Espacio para estudiantes apasionados por los números, álgebra, cálculo y matemática aplicada.",
            "member_count": 45,
        },
        {
            "name": "Futuros Educadores",
            "career": "Educación",
            "description": "Comunidad de estudiantes de educación comprometidos con transformar la enseñanza en el Perú.",
            "member_count": 62,
        },
        {
            "name": "Developers Peruanos",
            "career": "Informática",
            "description": "Club para estudiantes de sistemas, ingeniería de software y carreras tecnológicas.",
            "member_count": 78,
        },
        {
            "name": "Sociedad y Cambio",
            "career": "Ciencias Sociales",
            "description": "Análisis social, debates y propuestas para un mejor entendimiento de nuestra sociedad.",
            "member_count": 34,
        },
        {
            "name": "Poliglotas Unidos",
            "career": "Lenguas",
            "description": "Para estudiantes de idiomas, literatura y comunicación. Practicamos y compartimos culturas.",
            "member_count": 29,
        },
    ]

    for club_data in clubs_data:
        existing = Club.query.filter_by(name=club_data["name"]).first()
        if not existing:
            club = Club(**club_data)
            db.session.add(club)

    db.session.commit()
    print("✅ Clubes inicializados")


def init_events():
    """Initialize sample events"""
    events_data = [
        {
            "title": "Día del Apunte",
            "description": "Comparte tus mejores apuntes y gana Crolars extra. Durante todo el día, cada apunte subido te otorgará el doble de recompensas.",
            "event_date": datetime.now() + timedelta(days=30),
            "is_featured": True,
            "rewards": "Doble Crolars por apunte subido",
            "category": "Especial",
        },
        {
            "title": "Hackathon Educativo",
            "description": "Competencia de 48 horas para crear soluciones innovadoras en educación.",
            "event_date": datetime.now() + timedelta(days=45),
            "is_featured": True,
            "rewards": "500 Crolars al ganador",
            "category": "Competencia",
        },
        {
            "title": "Semana de la Ciencia",
            "description": "Celebra la ciencia compartiendo experimentos, proyectos y descubrimientos.",
            "event_date": datetime.now() + timedelta(days=60),
            "rewards": "Logros especiales disponibles",
            "category": "Académico",
        },
    ]

    for event_data in events_data:
        existing = Event.query.filter_by(title=event_data["title"]).first()
        if not existing:
            event = Event(**event_data)
            db.session.add(event)

    db.session.commit()
    print("✅ Eventos inicializados")


def init_forum_questions():
    """Initialize sample forum questions"""
    # Get the first user to assign as author
    user = User.query.first()
    if not user:
        print("❌ No hay usuarios. Crea al menos un usuario primero.")
        return

    questions_data = [
        {
            "title": "¿Cómo resolver integrales por partes?",
            "content": "Tengo dificultades para entender cuándo aplicar la integración por partes. ¿Podrían ayudarme con algunos ejemplos?",
            "category": "Matemáticas",
            "author_id": user.id,
        },
        {
            "title": "Mejores técnicas de estudio para memorización",
            "content": "¿Cuáles son las técnicas más efectivas para memorizar gran cantidad de información para los exámenes?",
            "category": "Otros",
            "author_id": user.id,
        },
        {
            "title": "Diferencia entre Python y JavaScript",
            "content": "Soy nuevo en programación. ¿Podrían explicarme las principales diferencias entre Python y JavaScript?",
            "category": "Tecnología",
            "author_id": user.id,
        },
    ]

    for question_data in questions_data:
        existing = ForumQuestion.query.filter_by(title=question_data["title"]).first()
        if not existing:
            question = ForumQuestion(**question_data)
            db.session.add(question)

    db.session.commit()
    print("✅ Preguntas del foro inicializadas")


def main():
    """Initialize all sample data"""
    app = create_app()
    with app.app_context():
        print("🚀 Inicializando datos de ejemplo para las nuevas secciones...")

        try:
            init_clubs()
            init_events()
            init_forum_questions()

            print(
                "\n✅ ¡Todos los datos de ejemplo han sido inicializados correctamente!"
            )
            print("\n📋 Resumen:")
            print(f"   • Clubes: {Club.query.count()}")
            print(f"   • Eventos: {Event.query.count()}")
            print(f"   • Preguntas del foro: {ForumQuestion.query.count()}")

        except Exception as e:
            print(f"❌ Error al inicializar datos: {e}")
            db.session.rollback()


if __name__ == "__main__":
    main()
