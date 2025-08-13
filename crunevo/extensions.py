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
import os

# Redis client setup
class MockRedis:
    def __init__(self):
        self._data = {}
    
    def get(self, key):
        return self._data.get(key)
    
    def set(self, key, value, ex=None):
        self._data[key] = value
        return True
    
    def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)
        return len(keys)
    
    def exists(self, key):
        return key in self._data
    
    def flushdb(self):
        self._data.clear()
        return True
    
    def ping(self):
        return True

try:
    import redis
    # Try to connect to Redis, fallback to mock if not available
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    # Test connection
    redis_client.ping()
except Exception:
    # Fallback to mock for development (handles ImportError, ConnectionError, etc.)
    redis_client = MockRedis()
# BEGIN: make eventlet optional for local dev compatibility
USE_EVENTLET = False
# Check if eventlet is disabled via environment variable (for serverless)
if not os.environ.get('DISABLE_EVENTLET'):
    try:
        from eventlet import websocket  # type: ignore
        from eventlet.greenio.base import shutdown_safe  # type: ignore
        USE_EVENTLET = True
    except Exception:
        websocket = None  # type: ignore
        shutdown_safe = None  # type: ignore
else:
    websocket = None  # type: ignore
    shutdown_safe = None  # type: ignore
# END: make eventlet optional for local dev compatibility

# Centralized extensions so models and blueprints can import `db`, `migrate` and
# `login_manager` without causing circular imports.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
# Relax default rate limits to avoid blocking normal usage
limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per day"])
talisman = Talisman()
# Use eventlet for async WebSocket support

# Patch eventlet.websocket to ignore EBADF errors when closing sockets


def _safe_close_ws(self):
    try:
        self._send_closing_frame(True)
        shutdown_safe(self.socket)  # type: ignore
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
        shutdown_safe(self.socket)  # type: ignore
    except OSError as e:  # pragma: no cover - avoid noisy logs on disconnect
        if e.errno not in (errno.ENOTCONN, errno.EBADF, errno.ENOTSOCK):
            self.log.write(
                "{ctx} socket shutdown error: {e}".format(ctx=self.log_context, e=e)
            )
    finally:
        self.socket.close()


# Only patch when eventlet is available
if USE_EVENTLET and websocket is not None:
    websocket.WebSocket.close = _safe_close_ws
    websocket.RFC6455WebSocket.close = _safe_close_rfc

# Initialize SocketIO with a compatible async_mode
socketio = SocketIO(async_mode=("eventlet" if USE_EVENTLET else "threading"))
oauth = OAuth()
