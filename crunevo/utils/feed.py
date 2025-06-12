from crunevo.extensions import db
from crunevo.models import User, FeedItem
import json


def create_feed_item_for_all(item_type, ref_id, metadata=None, owner_ids=None, is_highlight=False):
    """Create feed items for all or selected users.

    TODO: move to async task queue when feed grows.
    """
    if owner_ids is None:
        owner_ids = [u.id for u in User.query.with_entities(User.id).all()]

    meta_str = json.dumps(metadata) if metadata else None

    items = [
        FeedItem(
            owner_id=uid,
            item_type=item_type,
            ref_id=ref_id,
            meta=meta_str,
            is_highlight=is_highlight,
        )
        for uid in owner_ids
    ]
    if items:
        db.session.bulk_save_objects(items)
        db.session.commit()

