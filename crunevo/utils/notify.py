from crunevo.models.notification import Notification
from crunevo.extensions import db


def send_notification(user_id, message, url=None):
    notif = Notification(user_id=user_id, message=message, url=url)
    db.session.add(notif)
    db.session.commit()
