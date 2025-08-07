from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc

from crunevo.extensions import db
from crunevo.models import (
    FeedItem,
    Post,
    PostReaction,
    Note,
    User,
    UserAchievement,
    Credit,
)
from crunevo.utils.login_streak import streak_reward


def get_featured_posts():
    """Return top notes, posts and users with recent achievements."""
    top_notes = Note.query.order_by(Note.views.desc()).limit(3).all()
    top_posts = (
        Post.query.join(PostReaction)
        .group_by(Post.id)
        .order_by(func.count(PostReaction.id).desc())
        .limit(3)
        .all()
    )
    top_users = (
        db.session.query(User)
        .join(UserAchievement)
        .group_by(User.id)
        .order_by(func.max(UserAchievement.timestamp).desc())
        .limit(3)
        .all()
    )
    return top_notes, top_posts, top_users


def get_weekly_top_posts(limit=3):
    """Return posts with most likes from the last week."""
    last_week = datetime.utcnow() - timedelta(days=7)
    return (
        Post.query.join(PostReaction)
        .filter(Post.created_at > last_week)
        .group_by(Post.id)
        .order_by(func.count(PostReaction.id).desc())
        .limit(limit)
        .all()
    )


def get_weekly_ranking(limit=5):
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    top_ranked = (
        db.session.query(
            User.username,
            func.coalesce(func.sum(Credit.amount), 0).label("credits"),
        )
        .join(Credit, Credit.user_id == User.id)
        .filter(Credit.timestamp >= week_start)
        .group_by(User.id)
        .order_by(desc("credits"))
        .limit(limit)
        .all()
    )

    recent_achievements = (
        db.session.query(
            User.username, UserAchievement.badge_code, UserAchievement.timestamp
        )
        .join(User, User.id == UserAchievement.user_id)
        .order_by(UserAchievement.timestamp.desc())
        .limit(limit)
        .all()
    )
    return top_ranked, recent_achievements


def fetch_feed_data(user, categoria: str | None = None, limit: int = 10):
    query = FeedItem.query.filter_by(owner_id=user.id).options(
        joinedload(FeedItem.post), joinedload(FeedItem.note)
    )
    if categoria == "apuntes":
        query = query.filter_by(item_type="apunte")
    else:
        query = query.filter(FeedItem.item_type != "apunte")
    items_raw = query.order_by(FeedItem.created_at.desc()).limit(limit).all()

    feed_items: list[dict] = []
    post_ids: list[int] = []
    for item in items_raw:
        if item.item_type == "post" and item.post:
            if categoria == "imagen" and (
                not item.post.file_url or item.post.file_url.endswith(".pdf")
            ):
                continue
            feed_items.append({"type": "post", "data": item.post})
            post_ids.append(item.post.id)
        elif item.item_type == "apunte" and item.note and categoria == "apuntes":
            feed_items.append({"type": "note", "data": item.note})

    reaction_map = PostReaction.counts_for_posts(post_ids)
    user_reactions = PostReaction.reactions_for_user_posts(user.id, post_ids)

    from crunevo.models import SavedPost

    saved_posts = {
        sp.post_id: True
        for sp in SavedPost.query.filter(
            SavedPost.user_id == user.id,
            SavedPost.post_id.in_(post_ids),
        ).all()
    }

    trending_posts = get_weekly_top_posts(limit=3)
    trending_counts = PostReaction.counts_for_posts([p.id for p in trending_posts])
    trending_user_reactions = PostReaction.reactions_for_user_posts(
        user.id, [p.id for p in trending_posts]
    )

    return {
        "feed_items": feed_items,
        "reaction_counts": reaction_map,
        "user_reactions": user_reactions,
        "saved_posts": saved_posts,
        "trending_posts": trending_posts,
        "trending_counts": trending_counts,
        "trending_user_reactions": trending_user_reactions,
    }


def streak_info(user):
    streak = user.login_streak
    show_streak = (
        streak
        and streak.last_login == date.today()
        and streak.claimed_today != date.today()
    )
    reward = streak_reward(streak.current_day) if streak else 0
    return streak, show_streak, reward
