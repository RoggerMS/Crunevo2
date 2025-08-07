#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from crunevo import create_app
from crunevo.extensions import db
from crunevo.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Find the user
    user = User.query.filter_by(username='estudiante').first()
    
    if user:
        print(f"Found user: {user.username}")
        print(f"Current password hash: {user.password_hash[:50]}...")
        
        # Update password to 'test' using the User model method
        new_password = 'test'
        user.set_password(new_password)
        
        try:
            db.session.commit()
            print(f"✅ Password updated successfully!")
            print(f"New password: {new_password}")
            
            # Test the password
            if user.check_password(new_password):
                print("✅ Password verification successful!")
            else:
                print("❌ Password verification failed!")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating password: {e}")
    else:
        print("❌ User 'estudiante' not found")