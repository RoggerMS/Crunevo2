from flask import request
from flask_socketio import Namespace, emit

from ..extensions import socketio

connected_sessions = set()


class OnlineNamespace(Namespace):
    def on_connect(self):
        connected_sessions.add(request.sid)
        emit("count", {"count": len(connected_sessions)}, broadcast=True)

    def on_disconnect(self):
        connected_sessions.discard(request.sid)
        emit("count", {"count": len(connected_sessions)}, broadcast=True)


socketio.on_namespace(OnlineNamespace("/online"))
