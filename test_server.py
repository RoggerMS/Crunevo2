#!/usr/bin/env python3
"""
Script para probar la aplicación localmente con el DispatcherMiddleware
"""

from werkzeug.serving import run_simple
from crunevo.wsgi import application

if __name__ == '__main__':
    print("Iniciando servidor de prueba en http://0.0.0.0:8080")
    print("Presiona Ctrl+C para detener")
    run_simple(
        hostname='0.0.0.0',
        port=8080,
        application=application,
        use_debugger=True,
        use_reloader=True
    )