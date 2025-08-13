#!/usr/bin/env python3
"""
Script to create sample challenges for testing the social features
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models.social import Challenge, ChallengeType

def create_sample_challenges():
    """Create sample challenges for testing"""
    app = create_app()
    
    with app.app_context():
        # Check if challenges already exist
        existing_challenges = Challenge.query.count()
        if existing_challenges > 0:
            print(f"Found {existing_challenges} existing challenges. Skipping creation.")
            return
        
        # Create sample challenges
        challenges = [
            # Daily challenges
            {
                "title": "Responde 3 preguntas",
                "description": "Ayuda a otros estudiantes respondiendo 3 preguntas hoy",
                "challenge_type": ChallengeType.DAILY,
                "target_action": "answer_question",
                "target_value": 3,
                "reward_crolars": 50,
                "start_date": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                "end_date": datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            {
                "title": "Obtén 2 votos útiles",
                "description": "Recibe votos útiles en tus respuestas",
                "challenge_type": ChallengeType.DAILY,
                "target_action": "helpful_vote",
                "target_value": 2,
                "reward_crolars": 30,
                "start_date": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                "end_date": datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            {
                "title": "Haz una pregunta de calidad",
                "description": "Formula una pregunta bien estructurada con contexto completo",
                "challenge_type": ChallengeType.DAILY,
                "target_action": "ask_question",
                "target_value": 1,
                "reward_crolars": 25,
                "start_date": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                "end_date": datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            {
                "title": "Inicia sesión diariamente",
                "description": "Mantén tu racha de conexión diaria",
                "challenge_type": ChallengeType.DAILY,
                "target_action": "daily_login",
                "target_value": 1,
                "reward_crolars": 10,
                "start_date": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                "end_date": datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
            },
            
            # Weekly challenges
            {
                "title": "Mentor de la semana",
                "description": "Obtén 10 votos útiles en tus respuestas esta semana",
                "challenge_type": ChallengeType.WEEKLY,
                "target_action": "helpful_vote",
                "target_value": 10,
                "reward_crolars": 200,
                "start_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
                "end_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()) + timedelta(days=6, hours=23, minutes=59, seconds=59)
            },
            {
                "title": "Explorador de conocimiento",
                "description": "Responde preguntas en 5 materias diferentes esta semana",
                "challenge_type": ChallengeType.WEEKLY,
                "target_action": "answer_different_subjects",
                "target_value": 5,
                "reward_crolars": 150,
                "start_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
                "end_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()) + timedelta(days=6, hours=23, minutes=59, seconds=59)
            },
            {
                "title": "Estudiante activo",
                "description": "Haz 15 preguntas de calidad esta semana",
                "challenge_type": ChallengeType.WEEKLY,
                "target_action": "ask_question",
                "target_value": 15,
                "reward_crolars": 180,
                "start_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
                "end_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()) + timedelta(days=6, hours=23, minutes=59, seconds=59)
            },
            {
                "title": "Experto en matemáticas",
                "description": "Responde 20 preguntas de matemáticas correctamente",
                "challenge_type": ChallengeType.WEEKLY,
                "target_action": "answer_math_questions",
                "target_value": 20,
                "reward_crolars": 250,
                "start_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
                "end_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()) + timedelta(days=6, hours=23, minutes=59, seconds=59)
            },
            {
                "title": "Colaborador social",
                "description": "Participa en 3 grupos de estudio diferentes",
                "challenge_type": ChallengeType.WEEKLY,
                "target_action": "join_study_groups",
                "target_value": 3,
                "reward_crolars": 120,
                "start_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
                "end_date": datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()) + timedelta(days=6, hours=23, minutes=59, seconds=59)
            }
        ]
        
        for challenge_data in challenges:
            challenge = Challenge(**challenge_data)
            db.session.add(challenge)
        
        try:
            db.session.commit()
            print(f"Successfully created {len(challenges)} sample challenges!")
            
            # Print created challenges
            print("\nCreated challenges:")
            daily_challenges = Challenge.query.filter_by(challenge_type=ChallengeType.DAILY).all()
            weekly_challenges = Challenge.query.filter_by(challenge_type=ChallengeType.WEEKLY).all()
            
            print(f"\nDaily challenges ({len(daily_challenges)}):")
            for challenge in daily_challenges:
                print(f"- {challenge.title} ({challenge.reward_crolars} Crolars)")
                
            print(f"\nWeekly challenges ({len(weekly_challenges)}):")
            for challenge in weekly_challenges:
                print(f"- {challenge.title} ({challenge.reward_crolars} Crolars)")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error creating challenges: {e}")

if __name__ == "__main__":
    create_sample_challenges()