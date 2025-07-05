from datetime import datetime
from crunevo.extensions import db
from crunevo.models import Story


def cleanup_stories() -> None:
    Story.query.filter(Story.expires_at <= datetime.utcnow()).delete()
    db.session.commit()
