from crunevo.models import User
from crunevo.tasks import task_queue, insert_feed_items


def create_feed_item_for_all(
    item_type, ref_id, meta_dict=None, owner_ids=None, is_highlight=False
):
    """Enqueue creation of feed items for all or selected users."""
    if owner_ids is None:
        owner_ids = [u.id for u in User.query.with_entities(User.id).all()]

    task_queue.enqueue(
        insert_feed_items,
        item_type,
        ref_id,
        meta_dict,
        owner_ids,
        is_highlight,
    )
