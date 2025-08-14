#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Check if user already exists
    existing_user = User.query.filter_by(username="estudiante").first()

    if existing_user:
        print(f"User 'estudiante' already exists with ID: {existing_user.id}")
        print(f"Email: {existing_user.email}")
        print(f"Activated: {existing_user.activated}")
        print(f"Role: {existing_user.role}")
    else:
        # Create new user
        user = User(
            username="estudiante",
            email="estudiante@test.com",
            password_hash=generate_password_hash("estudiante123"),
            activated=True,
            role="user",
            first_name="Test",
            last_name="Student",
            university="Universidad de Prueba",
            career="Ingeniería de Sistemas",
        )

        try:
            db.session.add(user)
            db.session.commit()
            print("✅ User 'estudiante' created successfully!")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print("Password: estudiante123")
            print(f"ID: {user.id}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating user: {e}")
