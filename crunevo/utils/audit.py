from flask import request
from datetime import datetime
import json

from crunevo.extensions import db
from crunevo.models import AuthEvent


def record_auth_event(user, event_type, extra=None):
    token = request.headers.get("X-Device-Token")
    if token:
        try:
            data = json.loads(extra) if extra else {}
        except Exception:
            data = {"info": extra}
        data["device_token"] = token
        extra = json.dumps(data)

    ev = AuthEvent(
        user_id=user.id if user else None,
        event_type=event_type,
        ip=request.remote_addr,
        ua=request.headers.get("User-Agent"),
        extra=extra,
        timestamp=datetime.utcnow(),
    )
    db.session.add(ev)
    db.session.commit()
