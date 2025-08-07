#!/usr/bin/env python3

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models.user import User
from crunevo.models.post import Post
from crunevo.models.comment import Comment
from crunevo.models.login_history import LoginHistory
from crunevo.models.login_streak import LoginStreak

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Creando todas las tablas en PostgreSQL...")
        try:
            # Crear todas las tablas
            db.create_all()
            print("Tablas creadas exitosamente.")
            
            # Verificar si el usuario estudiante ya existe
            existing_user = User.query.filter_by(username='estudiante').first()
            
            if existing_user:
                print(f"El usuario 'estudiante' ya existe con ID: {existing_user.id}")
            else:
                # Crear el usuario estudiante
                student_user = User(
                    username='estudiante',
                    email='estudiante@crunevo.com',
                    role='student'
                )
                student_user.set_password('test')
                
                db.session.add(student_user)
                db.session.commit()
                print(f"Usuario 'estudiante' creado exitosamente con ID: {student_user.id}")
                print(f"Email: {student_user.email}")
                print(f"Contraseña: test")
                
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()