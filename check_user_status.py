#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models import User

app = create_app()

with app.app_context():
    # Find the user
    user = User.query.filter_by(username='estudiante').first()
    
    if user:
        print(f"User found: {user.username}")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Activated: {user.activated}")
        print(f"Role: {user.role}")
        print(f"About: {user.about}")
        print(f"Points: {user.points}")
        print(f"Credits: {user.credits}")
        print(f"Career: {user.career}")
        print(f"Verification level: {user.verification_level}")
        
        # Test password
        if user.check_password('test'):
            print("\n✅ Password 'test' is correct!")
        else:
            print("\n❌ Password 'test' is incorrect!")
            
        # Update activation status if needed
        if not user.activated:
            print("\n⚠️ User is not activated. Activating now...")
            user.activated = True
            try:
                db.session.commit()
                print("✅ User activated successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error activating user: {e}")
        else:
            print("\n✅ User is already activated.")
    else:
        print("❌ User 'estudiante' not found in database.")