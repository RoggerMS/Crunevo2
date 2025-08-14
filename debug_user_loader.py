from crunevo import create_app
from crunevo.models import User

app = create_app()

with app.app_context():
    print("=== Debug User Loader ===")

    # Check if user exists
    user = User.query.filter_by(username="estudiante").first()
    if user:
        print(f"✅ User found: {user.username} (ID: {user.id})")
        print(f"   Email: {user.email}")
        print(f"   Activated: {user.activated}")
        print(f"   Role: {user.role}")
        print(f"   Password hash: {user.password_hash[:50]}...")

        # Test password verification
        try:
            password_valid = user.check_password("test")
            print(f"   Password 'test' valid: {password_valid}")
        except Exception as e:
            print(f"   ❌ Password check error: {e}")

        # Test user loader function
        from crunevo.models.user import load_user

        try:
            loaded_user = load_user(str(user.id))
            if loaded_user:
                print(f"✅ User loader works: {loaded_user.username}")
                print(f"   Loaded user activated: {loaded_user.activated}")
            else:
                print("❌ User loader returned None")
        except Exception as e:
            print(f"❌ User loader error: {e}")

        # Test UserMixin methods
        try:
            print(f"   is_authenticated: {user.is_authenticated}")
            print(f"   is_active: {user.is_active}")
            print(f"   is_anonymous: {user.is_anonymous}")
            print(f"   get_id(): {user.get_id()}")
        except Exception as e:
            print(f"❌ UserMixin methods error: {e}")

    else:
        print("❌ User 'estudiante' not found")

    # List all users
    print("\n=== All Users ===")
    all_users = User.query.all()
    for u in all_users:
        print(f"- {u.username} (ID: {u.id}, activated: {u.activated})")
