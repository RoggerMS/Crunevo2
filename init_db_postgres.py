#!/usr/bin/env python3

from crunevo import create_app
from crunevo.utils.db_init import init_database

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Inicializando base de datos PostgreSQL...")
        init_database()
        print("Base de datos inicializada exitosamente.")
