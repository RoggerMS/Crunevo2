# -*- coding: utf-8 -*-
from flask import url_for
from crunevo.models import (
    FeedItem,
    Post,
    SavedPost,
    PostComment,
    PostReaction,
)
from crunevo.utils.feed import create_feed_item_for_all
from crunevo.cache import feed_cache
from crunevo.utils.achievements import unlock_achievement
from crunevo.utils.credits import add_credit, spend_credit
from flask_login import login_user


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_feed_shows_post_for_other_user(client, db_session, test_user, another_user):
    post = Post(content="Feed post", author=test_user)
    db_session.add(post)
    db_session.commit()
    create_feed_item_for_all("post", post.id)

    login(client, another_user.username, "secret")
    resp = client.get("/api/feed")
    assert resp.status_code == 200
    data = resp.get_json()[0]
    assert data["item_type"] == "post"
    assert data["content"] == "Feed post"


def test_feed_includes_achievement_event(client, db_session, test_user, another_user):
    unlock_achievement(test_user, "badge_test")
    login(client, another_user.username, "secret")
    resp = client.get("/api/feed")
    assert resp.status_code == 200
    types = [d["item_type"] for d in resp.get_json()]
    assert "logro" in types


def test_self_spend_no_movement_feed(app, db_session, test_user):
    with app.test_request_context("/"):
        login_user(test_user)
        add_credit(test_user, 5, "test")
        spend_credit(test_user, 2, "test")
    assert FeedItem.query.count() == 0


def test_feed_cache_roundtrip(reset_caches):
    from datetime import datetime

    items = [
        {
            "score": 1.0,
            "created_at": datetime.utcnow(),
            "payload": {"hello": "world"},
        }
    ]
    feed_cache.push_items(42, items)
    assert feed_cache.fetch(42) == [{"hello": "world"}]


def test_push_items_persists(reset_caches):
    from datetime import datetime
    from crunevo.cache.feed_cache import push_items, fetch

    push_items(1, [{"score": 0, "created_at": datetime.utcnow(), "payload": {"a": 1}}])
    assert fetch(1)[0] == {"a": 1}


def test_feed_fetch_handles_error(monkeypatch, client, db_session, test_user):
    monkeypatch.setattr(
        feed_cache, "fetch", lambda *a, **k: (_ for _ in ()).throw(Exception("boom"))
    )
    login(client, test_user.username, "secret")
    resp = client.get("/api/feed")
    assert resp.status_code == 200


def test_feed_cache_hit_after_warmup(reset_caches, client, test_user, monkeypatch):
    login(client, test_user.username, "secret")
    warm = client.get("/api/feed").get_json()

    class FakeQueryReturningNothing:
        def filter_by(self, *a, **k):
            return self

        def filter(self, *a, **k):
            return self

        def order_by(self, *a, **k):
            return self

        def offset(self, *a, **k):
            return self

        def limit(self, *a, **k):
            return self

        def all(self):
            return []

    with monkeypatch.context() as m:
        m.setattr(
            "crunevo.routes.feed_routes.FeedItem.query",
            FakeQueryReturningNothing(),
        )
        cached = client.get("/api/feed").get_json()
    assert cached == warm


def test_feed_ordering(reset_caches, client, db_session, test_user, another_user):
    post1 = Post(content="A", author=test_user)
    post2 = Post(content="B", author=test_user)
    db_session.add_all([post1, post2])
    db_session.commit()
    create_feed_item_for_all("post", post1.id)
    create_feed_item_for_all("post", post2.id)

    login(client, another_user.username, "secret")
    client.post(f"/feed/like/{post1.id}")
    resp = client.get("/api/feed")
    contents = [it["content"] for it in resp.get_json() if it["item_type"] == "post"]
    assert contents == ["B", "A"]


def test_view_post(client, db_session, test_user):
    post = Post(content="hello", author=test_user)
    db_session.add(post)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.get(f"/post/{post.id}")
    assert resp.status_code == 200
    assert b"hello" in resp.data


def test_view_post_alias(client, db_session, test_user):
    """Ensure /posts/<id> alias works for view_post."""
    post = Post(content="alias", author=test_user)
    db_session.add(post)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.get(f"/posts/{post.id}")
    assert resp.status_code == 200
    assert b"alias" in resp.data


def test_url_for_view_post(app):
    with app.app_context():
        with app.test_request_context():
            assert url_for("feed.view_post", post_id=42) == "/post/42"


def test_eliminar_post_authorized(client, db_session, test_user):
    post = Post(content="del", author=test_user)
    db_session.add(post)
    db_session.commit()
    create_feed_item_for_all("post", post.id)

    login(client, test_user.username, "secret")
    resp = client.post(f"/feed/post/eliminar/{post.id}")
    assert resp.status_code == 302
    assert Post.query.get(post.id) is None
    assert not any(i.get("ref_id") == post.id for i in feed_cache.fetch(test_user.id))


def test_eliminar_post_forbidden(client, db_session, test_user, another_user):
    post = Post(content="del", author=test_user)
    db_session.add(post)
    db_session.commit()
    create_feed_item_for_all("post", post.id)

    login(client, another_user.username, "secret")
    resp = client.post(f"/feed/post/eliminar/{post.id}")
    assert resp.status_code == 403
    assert Post.query.get(post.id) is not None


def test_eliminar_post_with_saved_posts(client, db_session, test_user, another_user):
    post = Post(content="del2", author=test_user)
    db_session.add(post)
    db_session.commit()
    create_feed_item_for_all("post", post.id)

    saved = SavedPost(user_id=another_user.id, post_id=post.id)
    db_session.add(saved)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.post(f"/feed/post/eliminar/{post.id}")
    assert resp.status_code == 302
    assert Post.query.get(post.id) is None
    assert SavedPost.query.filter_by(post_id=post.id).count() == 0


def test_eliminar_post_with_reactions(client, db_session, test_user, another_user):
    post = Post(content="r", author=test_user)
    db_session.add(post)
    db_session.commit()
    create_feed_item_for_all("post", post.id)

    comment = PostComment(body="c", author=another_user, post=post)
    reaction = PostReaction(
        user_id=another_user.id, post_id=post.id, reaction_type="like"
    )
    db_session.add(comment)
    db_session.add(reaction)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.post(f"/feed/post/eliminar/{post.id}")
    assert resp.status_code == 302
    assert Post.query.get(post.id) is None
    assert PostComment.query.filter_by(post_id=post.id).count() == 0
    assert PostReaction.query.filter_by(post_id=post.id).count() == 0


def test_feed_load_empty_returns_message(client, test_user):
    login(client, test_user.username, "secret")
    resp = client.get("/feed/load?page=99")
    assert resp.status_code == 200
    assert "No hay más publicaciones." in resp.data.decode("utf-8")
