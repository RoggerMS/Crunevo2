from datetime import datetime, timedelta

from crunevo.extensions import db
from crunevo.models import AuthEvent


def cleanup_auth_events(days: int = 90) -> None:
    cutoff = datetime.utcnow() - timedelta(days=days)
    AuthEvent.query.filter(AuthEvent.timestamp < cutoff).delete()
    db.session.commit()
