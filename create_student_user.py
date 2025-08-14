#!/usr/bin/env python3
"""
Script para crear el usuario estudiante con password test
"""

import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crunevo.app import create_app
from crunevo.extensions import db
from crunevo.models.user import User


def create_student_user():
    """Crear el usuario estudiante si no existe"""
    app = create_app()

    with app.app_context():
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(username="estudiante").first()

        if existing_user:
            print(f"El usuario 'estudiante' ya existe con ID: {existing_user.id}")
            print(f"Email: {existing_user.email}")
            print(f"Activado: {existing_user.activated}")
            return existing_user

        # Crear el nuevo usuario
        student_user = User(
            username="estudiante",
            email="estudiante@crunevo.com",
            role="student",
            activated=True,  # Activar directamente para poder hacer login
            points=0,
            credits=0,
            chat_enabled=True,
            verification_level=0,
        )

        # Establecer la contraseña
        student_user.set_password("test")

        # Agregar a la base de datos
        db.session.add(student_user)
        db.session.commit()

        print(f"Usuario 'estudiante' creado exitosamente con ID: {student_user.id}")
        print(f"Email: {student_user.email}")
        print("Password: test")
        print(f"Activado: {student_user.activated}")

        return student_user


if __name__ == "__main__":
    create_student_user()
