from flask import request
from flask_socketio import Namespace, emit

from ..extensions import socketio

connected_sessions = set()


class OnlineNamespace(Namespace):
    def on_connect(self):
        connected_sessions.add(request.sid)
        emit("count", {"count": len(connected_sessions)}, broadcast=True)

    def on_disconnect(self, sid=None, *args):
        # Flask-SocketIO may pass the session id and a reason argument when the
        # client disconnects. Accept optional parameters to avoid TypeError.
        session_id = sid or request.sid
        connected_sessions.discard(session_id)
        emit("count", {"count": len(connected_sessions)}, broadcast=True)


socketio.on_namespace(OnlineNamespace("/online"))
