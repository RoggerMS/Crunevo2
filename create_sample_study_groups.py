#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear grupos de estudio de ejemplo en Crunevo
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models.social import StudyGroup, StudyGroupMember


def create_sample_study_groups():
    """Crear grupos de estudio de ejemplo"""
    app = create_app()

    with app.app_context():
        # Verificar si ya existen grupos de estudio
        existing_groups = StudyGroup.query.count()
        if existing_groups > 0:
            print(
                f"Ya existen {existing_groups} grupos de estudio en la base de datos."
            )
            return

        # Obtener un usuario existente para usar como creador
        try:
            # Usar ID 1 directamente para evitar problemas de consulta
            creator_id = 1
            print(f"Using user ID {creator_id} as group creator")
        except Exception as e:
            print(f"Error getting user: {e}")
            return

        # Grupos de estudio de ejemplo
        study_groups = [
            {
                "name": "Matemáticas Avanzadas",
                "description": "Grupo para estudiar cálculo, álgebra lineal y matemáticas discretas. Nos reunimos para resolver ejercicios y preparar exámenes.",
                "subject": "Matemáticas",
                "max_members": 8,
                "creator_id": creator_id,
                "is_active": True,
            },
            {
                "name": "Programación Web",
                "description": "Aprendemos desarrollo web con HTML, CSS, JavaScript y frameworks modernos. Proyectos colaborativos y code reviews.",
                "subject": "Programación",
                "max_members": 6,
                "creator_id": creator_id,
                "is_active": True,
            },
            {
                "name": "Ciencias Naturales",
                "description": "Estudio conjunto de Biología, Química y Física. Experimentos virtuales y preparación para olimpiadas científicas.",
                "subject": "Ciencias",
                "max_members": 10,
                "creator_id": creator_id,
                "is_active": True,
            },
            {
                "name": "Historia Mundial",
                "description": "Análisis de eventos históricos importantes, debates sobre causas y consecuencias, y técnicas de memorización.",
                "subject": "Historia",
                "max_members": 12,
                "creator_id": creator_id,
                "is_active": True,
            },
            {
                "name": "Literatura Clásica",
                "description": "Lectura y análisis de obras literarias clásicas. Discusiones sobre temas, personajes y técnicas narrativas.",
                "subject": "Literatura",
                "max_members": 7,
                "creator_id": creator_id,
                "is_active": True,
            },
            {
                "name": "Inglés Conversacional",
                "description": "Práctica de conversación en inglés, gramática avanzada y preparación para exámenes internacionales.",
                "subject": "Idiomas",
                "max_members": 5,
                "creator_id": creator_id,
                "is_active": True,
            },
        ]

        # Crear grupos de estudio
        created_count = 0
        group_ids = []

        for group_data in study_groups:
            study_group = StudyGroup(**group_data)
            db.session.add(study_group)
            db.session.flush()  # Para obtener el ID
            group_ids.append(study_group.id)
            created_count += 1

        # Agregar el creador como miembro de cada grupo
        for group_id in group_ids:
            member = StudyGroupMember(
                group_id=group_id, user_id=creator_id, is_active=True
            )
            db.session.add(member)

        try:
            db.session.commit()
            print(f"Successfully created {created_count} sample study groups!")

            # Mostrar grupos creados
            print("\nCreated study groups:")
            for group in StudyGroup.query.all():
                member_count = len(group.members)
                status = "active" if group.is_active else "inactive"
                print(
                    f"- {group.name} ({group.subject}) - {member_count}/{group.max_members} members - {status}"
                )

        except Exception as e:
            db.session.rollback()
            print(f"Error creating study groups: {e}")
            raise


if __name__ == "__main__":
    create_sample_study_groups()
