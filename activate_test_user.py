from crunevo.app import create_app
from crunevo.extensions import db
from crunevo.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='usuario.prueba@test.com').first()
    if user:
        print(f'Usuario encontrado: {user.email}')
        user.activated = True
        db.session.commit()
        print('Usuario activado exitosamente')
    else:
        print('Usuario no encontrado')