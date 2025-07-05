from crunevo.models.notification import Notification
from crunevo.extensions import db
from crunevo.models import User


def send_notification(
    user_id=None, message=None, url=None, career=None, interests=None
):
    """Send a notification to a single user or a filtered group."""
    if user_id is not None:
        users = User.query.filter_by(id=user_id).all()
    else:
        query = User.query
        if career:
            query = query.filter_by(career=career)
        if interests:
            query = query.filter(User.interests.ilike(f"%{interests}%"))
        users = query.all()

    for u in users:
        db.session.add(Notification(user_id=u.id, message=message, url=url))

    db.session.commit()
