#!/usr/bin/env python3
"""
Script to create sample competitions for testing the social features
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models.social import Competition, CompetitionStatus

def create_sample_competitions():
    """Create sample competitions for testing"""
    app = create_app()
    
    with app.app_context():
        # Check if competitions already exist
        existing_competitions = Competition.query.count()
        if existing_competitions > 0:
            print(f"Found {existing_competitions} existing competitions. Skipping creation.")
            return
        
        # Get a user to be the creator of competitions
        creator_user = db.session.execute(db.text('SELECT id FROM user LIMIT 1')).fetchone()
        if not creator_user:
            print("No users found. Please create a user first.")
            return
        
        creator_id = creator_user[0]
        print(f"Using user ID {creator_id} as competition creator")
        
        # Create sample competitions
        competitions = [
            {
                "title": "Olimpiada de Matemáticas",
                "description": "Competencia de resolución de problemas matemáticos avanzados. Demuestra tu habilidad resolviendo ecuaciones complejas y problemas de geometría.",
                "subject": "Matemáticas",
                "difficulty": "Avanzado",
                "prize_crolars": 500,
                "entry_fee": 50,
                "max_participants": 100,
                "start_date": datetime.utcnow() + timedelta(days=3),
                "end_date": datetime.utcnow() + timedelta(days=10),
                "status": CompetitionStatus.UPCOMING,
                "creator_id": creator_id
            },
            {
                "title": "Quiz de Ciencias Naturales",
                "description": "Pon a prueba tus conocimientos en biología, química y física. Preguntas de opción múltiple sobre conceptos fundamentales.",
                "subject": "Ciencias",
                "difficulty": "Intermedio",
                "prize_crolars": 300,
                "entry_fee": 25,
                "max_participants": 150,
                "start_date": datetime.utcnow() + timedelta(days=1),
                "end_date": datetime.utcnow() + timedelta(days=8),
                "status": CompetitionStatus.UPCOMING
            },
            {
                "title": "Hackathon de Programación",
                "description": "Desarrolla una aplicación web innovadora en 48 horas. Trabaja en equipo y demuestra tus habilidades de programación.",
                "subject": "Programación",
                "difficulty": "Avanzado",
                "prize_crolars": 1000,
                "entry_fee": 100,
                "max_participants": 50,
                "start_date": datetime.utcnow() + timedelta(days=7),
                "end_date": datetime.utcnow() + timedelta(days=9),
                "status": CompetitionStatus.UPCOMING
            },
            {
                "title": "Debate de Historia Universal",
                "description": "Participa en debates sobre eventos históricos significativos. Defiende tu posición con argumentos sólidos y evidencia histórica.",
                "subject": "Historia",
                "difficulty": "Intermedio",
                "prize_crolars": 250,
                "entry_fee": 20,
                "max_participants": 30,
                "start_date": datetime.utcnow() + timedelta(days=5),
                "end_date": datetime.utcnow() + timedelta(days=5),
                "status": CompetitionStatus.UPCOMING
            },
            {
                "title": "Concurso de Redacción",
                "description": "Escribe un ensayo creativo sobre un tema de actualidad. Demuestra tu capacidad de análisis y expresión escrita.",
                "subject": "Literatura",
                "difficulty": "Básico",
                "prize_crolars": 200,
                "entry_fee": 15,
                "max_participants": 80,
                "start_date": datetime.utcnow() + timedelta(days=2),
                "end_date": datetime.utcnow() + timedelta(days=14),
                "status": CompetitionStatus.UPCOMING
            },
            {
                "title": "Desafío de Física Cuántica",
                "description": "Resuelve problemas complejos de mecánica cuántica y física moderna. Solo para los más experimentados en física.",
                "subject": "Física",
                "difficulty": "Avanzado",
                "prize_crolars": 750,
                "entry_fee": 75,
                "max_participants": 40,
                "start_date": datetime.utcnow() - timedelta(days=2),
                "end_date": datetime.utcnow() + timedelta(days=5),
                "status": CompetitionStatus.ACTIVE
            }
        ]
        
        for comp_data in competitions:
            # Add creator_id if not already present
            if 'creator_id' not in comp_data:
                comp_data['creator_id'] = creator_id
            competition = Competition(**comp_data)
            db.session.add(competition)
        
        try:
            db.session.commit()
            print(f"Successfully created {len(competitions)} sample competitions!")
            
            # Print created competitions
            print("\nCreated competitions:")
            for comp in Competition.query.all():
                print(f"- {comp.title} ({comp.subject}) - {comp.status.value}")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error creating competitions: {e}")

if __name__ == "__main__":
    create_sample_competitions()