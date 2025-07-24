from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from crunevo.app import create_app
from crunevo.extensions import talisman

# Creamos la aplicación principal
app = create_app()

# Creamos una mini-app súper ligera SOLO para el health check
health_app = Flask(__name__)


@health_app.route("/healthz")
@talisman(force_https=False)
def health():
    """Responde instantáneamente. No toca la base de datos ni la app principal."""
    return "ok", 200


# Usamos un Dispatcher para enrutar el tráfico.
# Si la petición es para /healthz, va a la app ligera.
# Para todo lo demás, va a la app principal.
application = DispatcherMiddleware(
    health_app,
    {
        "/": app,
    },
)
