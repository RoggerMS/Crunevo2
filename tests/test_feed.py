# -*- coding: utf-8 -*-
from flask import url_for
from crunevo.models import (
    FeedItem,
    Post,
    SavedPost,
    PostComment,
    PostReaction,
)
from io import BytesIO
from crunevo.utils.feed import create_feed_item_for_all
from crunevo.cache import feed_cache
from crunevo.utils.achievements import unlock_achievement
from crunevo.utils.credits import add_credit, spend_credit
from flask_login import login_user


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_create_post_rejects_invalid_extension(client, db_session, test_user):
    login(client, test_user.username, "secret")
    data = {"content": "hola", "files": (BytesIO(b"bad"), "file.exe")}
    resp = client.post(
        "/feed/post",
        data=data,
        content_type="multipart/form-data",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Archivo no permitido" in resp.get_data(as_text=True)
    assert Post.query.count() == 0


def test_create_post_rejects_large_file(client, db_session, test_user):
    login(client, test_user.username, "secret")
    big = BytesIO(b"a" * (6 * 1024 * 1024))
    data = {"content": "hola", "files": (big, "big.jpg")}
    resp = client.post(
        "/feed/post",
        data=data,
        content_type="multipart/form-data",
        headers={"Accept": "text/html"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Archivo no permitido" in resp.get_data(as_text=True)
    assert Post.query.count() == 0


def test_create_post_returns_html_snippet(client, db_session, test_user):
    login(client, test_user.username, "secret")
    resp = client.post(
        "/feed/post",
        data={"content": "hola"},
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "html" in data
    assert "hola" in data["html"]
    assert Post.query.count() == 1


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


def test_feed_cache_cleanup_removes_old_entries(reset_caches):

    from datetime import datetime, timedelta

    feed_cache.push_items(
        1, [{"score": 0, "created_at": datetime.utcnow(), "payload": {"a": 1}}]
    )

    feed_cache._cache[1][0]["cached_at"] = datetime.utcnow() - timedelta(
        seconds=feed_cache.CACHE_TTL + 1
    )

    feed_cache.cleanup()

    assert feed_cache.fetch(1) == []


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


def test_feed_second_page_has_new_posts(client, db_session, test_user, another_user):
    # Create multiple posts to populate more than one page
    posts = []
    for i in range(25):
        p = Post(content=f"post{i}", author=test_user)
        db_session.add(p)
        db_session.flush()
        create_feed_item_for_all("post", p.id)
        posts.append(p)
    db_session.commit()

    login(client, another_user.username, "secret")
    first_page = client.get("/feed/")
    assert first_page.status_code == 200
    first_html = first_page.data.decode("utf-8")

    # Ensure a middle post is not in the first page but appears on the second
    assert posts[14].content not in first_html

    second_page = client.get("/feed/load?page=2")
    assert second_page.status_code == 200
    second_html = second_page.data.decode("utf-8")
    assert posts[14].content in second_html


def test_comments_api_pagination(client, db_session, test_user):
    post = Post(content="c", author=test_user)
    db_session.add(post)
    db_session.commit()
    comments = [
        PostComment(body=f"c{i}", author=test_user, post=post) for i in range(15)
    ]
    db_session.add_all(comments)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp1 = client.get(f"/feed/api/comments/{post.id}?page=1")
    resp2 = client.get(f"/feed/api/comments/{post.id}?page=2")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    data1 = resp1.get_json()
    data2 = resp2.get_json()
    assert len(data1["comments"]) == 10
    assert data1["has_more"] is True
    assert len(data2["comments"]) == 5
    assert data2["has_more"] is False


def test_comment_disabled_returns_403(client, db_session, test_user, another_user):
    post = Post(content="x", author=test_user, comment_permission="none")
    db_session.add(post)
    db_session.commit()

    login(client, another_user.username, "secret")
    resp = client.post(f"/feed/comment/{post.id}", data={"body": "hello"})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "Comentarios deshabilitados"


def test_delete_own_comment(client, db_session, test_user):
    post = Post(content="d", author=test_user)
    db_session.add(post)
    db_session.commit()
    comment = PostComment(body="bye", author=test_user, post=post)
    db_session.add(comment)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.post(f"/feed/comment/delete/{comment.id}")
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    assert PostComment.query.get(comment.id) is None


def test_delete_comment_unauthorized(client, db_session, test_user, another_user):
    post = Post(content="x", author=test_user)
    db_session.add(post)
    db_session.commit()
    comment = PostComment(body="nope", author=another_user, post=post)
    db_session.add(comment)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.post(f"/feed/comment/delete/{comment.id}")
    assert resp.status_code == 403
    assert PostComment.query.get(comment.id) is not None
