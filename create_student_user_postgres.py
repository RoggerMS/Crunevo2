#!/usr/bin/env python3

from crunevo import create_app
from crunevo.models.user import User
from crunevo.extensions import db

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(username="estudiante").first()

        if existing_user:
            print(f"El usuario 'estudiante' ya existe con ID: {existing_user.id}")
        else:
            # Crear el usuario estudiante
            student_user = User(
                username="estudiante", email="estudiante@crunevo.com", role="student"
            )
            student_user.set_password("test")

            try:
                db.session.add(student_user)
                db.session.commit()
                print(
                    f"Usuario 'estudiante' creado exitosamente con ID: {student_user.id}"
                )
                print(f"Email: {student_user.email}")
                print("Contraseña: test")
            except Exception as e:
                db.session.rollback()
                print(f"Error al crear el usuario: {e}")
