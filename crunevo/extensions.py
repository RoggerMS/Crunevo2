from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_socketio import SocketIO
from authlib.integrations.flask_client import OAuth

import errno
from eventlet import websocket
from eventlet.greenio.base import shutdown_safe
import os

# Centralized extensions so models and blueprints can import `db`, `migrate` and
# `login_manager` without causing circular imports.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
# Rate limiting
try:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        default_limits=["200 per day", "50 per hour"],
        strategy="fixed-window",
    )
except Exception as e:
    print(f"Error inicializando rate limiter: {e}")
    limiter = None
# Talisman (opcional)
try:
    talisman = Talisman()
except Exception as e:
    print(f"Error inicializando Talisman: {e}")
    talisman = None
# Use eventlet for async WebSocket support

# Patch eventlet.websocket to ignore EBADF errors when closing sockets


def _safe_close_ws(self):
    try:
        self._send_closing_frame(True)
        shutdown_safe(self.socket)
    except OSError as e:  # pragma: no cover - avoid noisy logs on disconnect
        if e.errno not in (errno.ENOTCONN, errno.EBADF, errno.ENOTSOCK):
            self.log.write(
                "{ctx} socket shutdown error: {e}".format(ctx=self.log_context, e=e)
            )
    finally:
        self.socket.close()


def _safe_close_rfc(self, close_data=None):
    try:
        self._send_closing_frame(close_data=close_data, ignore_send_errors=True)
        shutdown_safe(self.socket)
    except OSError as e:  # pragma: no cover - avoid noisy logs on disconnect
        if e.errno not in (errno.ENOTCONN, errno.EBADF, errno.ENOTSOCK):
            self.log.write(
                "{ctx} socket shutdown error: {e}".format(ctx=self.log_context, e=e)
            )
    finally:
        self.socket.close()


websocket.WebSocket.close = _safe_close_ws
websocket.RFC6455WebSocket.close = _safe_close_rfc

socketio = SocketIO(async_mode="eventlet")
oauth = OAuth()

# Redis client (opcional)
try:
    import redis
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    # Test connection
    redis_client.ping()
except (ImportError, redis.ConnectionError, Exception):
    redis_client = None
    print("Redis no disponible, usando cache en memoria")
