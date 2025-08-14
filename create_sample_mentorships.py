#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear mentorías de ejemplo en Crunevo
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models.social import Mentorship
from crunevo.models.user import User


def create_sample_mentorships():
    """Crear mentorías de ejemplo"""
    app = create_app()

    with app.app_context():
        # Verificar si ya existen mentorías
        existing_mentorships = Mentorship.query.count()
        if existing_mentorships > 0:
            print(f"Ya existen {existing_mentorships} mentorías en la base de datos.")
            return

        # Obtener un usuario existente para usar como mentor
        try:
            user = User.query.first()
            if not user:
                print(
                    "No hay usuarios en la base de datos. Se necesita al menos 1 usuario."
                )
                return
            mentor_id = user.id
            print(f"Using user '{user.username}' (ID: {mentor_id}) as mentor")
        except Exception as e:
            print(f"Error getting user: {e}")
            # Usar ID 1 como fallback
            mentor_id = 1
            print(f"Using fallback mentor_id: {mentor_id}")

        # Mentorías de ejemplo (usando student_id = mentor_id para simplificar)
        mentorships = [
            {
                "mentor_id": mentor_id,
                "student_id": mentor_id,  # Usando el mismo ID para simplificar
                "subject_area": "Matemáticas",
                "message": "Solicito ayuda con álgebra, geometría y cálculo básico. Necesito apoyo para mejorar en matemáticas.",
            },
            {
                "mentor_id": mentor_id,
                "student_id": mentor_id,
                "subject_area": "Programación",
                "message": "Quiero aprender Python y JavaScript. Soy principiante en programación.",
            },
            {
                "mentor_id": mentor_id,
                "student_id": mentor_id,
                "subject_area": "Ciencias",
                "message": "Necesito ayuda con Biología, Química y Física para preparar exámenes.",
            },
            {
                "mentor_id": mentor_id,
                "student_id": mentor_id,
                "subject_area": "Historia",
                "message": "Busco apoyo en Historia universal y técnicas de estudio para memorizar fechas.",
            },
            {
                "mentor_id": mentor_id,
                "student_id": mentor_id,
                "subject_area": "Literatura",
                "message": "Requiero ayuda con análisis literario y redacción de ensayos.",
            },
        ]

        # Crear mentorías
        created_count = 0
        for mentorship_data in mentorships:
            mentorship = Mentorship(**mentorship_data)
            db.session.add(mentorship)
            created_count += 1

        try:
            db.session.commit()
            print(f"Successfully created {created_count} sample mentorships!")

            # Mostrar mentorías creadas
            print("\nCreated mentorships:")
            for mentorship in Mentorship.query.all():
                print(
                    f"- {mentorship.subject_area} (Status: {mentorship.status.value}) - ID: {mentorship.id}"
                )

        except Exception as e:
            db.session.rollback()
            print(f"Error creating mentorships: {e}")
            raise


if __name__ == "__main__":
    create_sample_mentorships()
