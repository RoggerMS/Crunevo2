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

# Centralized extensions so models and blueprints can import `db`, `migrate` and
# `login_manager` without causing circular imports.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day"])
talisman = Talisman()
# Use eventlet for async WebSocket support

# Patch eventlet.websocket to ignore EBADF errors when closing sockets


def _safe_close(self):
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


websocket.WebSocket.close = _safe_close

socketio = SocketIO(async_mode="eventlet")
oauth = OAuth()
