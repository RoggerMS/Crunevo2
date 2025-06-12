from flask import request
from datetime import datetime
from crunevo.extensions import db
from crunevo.models import AuthEvent


def record_auth_event(user, event_type):
    ev = AuthEvent(
        user_id=user.id if user else None,
        event_type=event_type,
        ip=request.remote_addr,
        ua=request.headers.get("User-Agent"),
        timestamp=datetime.utcnow(),
    )
    db.session.add(ev)
    db.session.commit()
