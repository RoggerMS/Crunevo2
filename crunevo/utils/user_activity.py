from datetime import datetime
from flask_login import current_user
from crunevo.extensions import db
from crunevo.models import UserActivity


def record_activity(
    action: str, target_id: int | None = None, target_type: str | None = None
):
    if not current_user.is_authenticated:
        return
    act = UserActivity(
        user_id=current_user.id,
        action=action,
        target_id=target_id,
        target_type=target_type,
        timestamp=datetime.utcnow(),
    )
    db.session.add(act)
    db.session.commit()
