from flask import url_for
from crunevo.models import Note, FeedItem, Post
from crunevo.utils.feed import create_feed_item_for_all
from crunevo.cache import feed_cache
from crunevo.utils.achievements import unlock_achievement
from crunevo.utils.credits import add_credit, spend_credit
from flask_login import login_user


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_feed_shows_note_for_other_user(client, db_session, test_user, another_user):
    note = Note(title="Feed note", author=test_user)
    db_session.add(note)
    db_session.commit()
    create_feed_item_for_all("apunte", note.id)

    login(client, another_user.username, "secret")
    resp = client.get("/api/feed")
    assert resp.status_code == 200
    data = resp.get_json()[0]
    assert data["item_type"] == "apunte"
    assert data["title"] == "Feed note"


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


def test_feed_cache_roundtrip(fake_redis):
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


def test_push_items_sets_ttl(fake_redis):
    from datetime import datetime
    from crunevo.cache.feed_cache import push_items, FEED_KEY

    push_items(1, [{"score": 0, "created_at": datetime.utcnow(), "payload": {}}])
    assert fake_redis.ttl(FEED_KEY.format(user_id=1)) > 0


def test_feed_fallback_on_redis_error(monkeypatch, client, db_session, test_user):
    from redis.exceptions import RedisError

    monkeypatch.setattr(
        feed_cache,
        "fetch",
        lambda *a, **k: (_ for _ in ()).throw(RedisError("boom")),
    )
    login(client, test_user.username, "secret")
    resp = client.get("/api/feed")
    assert resp.status_code == 200


def test_feed_cache_hit_after_warmup(fake_redis, client, test_user, monkeypatch):
    login(client, test_user.username, "secret")
    warm = client.get("/api/feed").get_json()

    class FakeQueryReturningNothing:
        def filter_by(self, *a, **k):
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


def test_feed_ordering(fake_redis, client, db_session, test_user, another_user):
    note1 = Note(title="A", author=test_user)
    note2 = Note(title="B", author=test_user)
    db_session.add_all([note1, note2])
    db_session.commit()
    create_feed_item_for_all("apunte", note1.id)
    create_feed_item_for_all("apunte", note2.id)

    login(client, another_user.username, "secret")
    client.post(f"/notes/{note1.id}/like")
    resp = client.get("/api/feed")
    titles = [it["title"] for it in resp.get_json() if it["item_type"] == "apunte"]
    assert titles[0] == "A"


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
