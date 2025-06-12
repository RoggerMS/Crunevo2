from crunevo.extensions import db
from crunevo.models import User, FeedItem


def create_feed_item_for_all(item_type, ref_id):
    user_ids = [u.id for u in User.query.with_entities(User.id).all()]
    items = [FeedItem(owner_id=uid, item_type=item_type, ref_id=ref_id) for uid in user_ids]
    if items:
        db.session.bulk_save_objects(items)
        db.session.commit()

