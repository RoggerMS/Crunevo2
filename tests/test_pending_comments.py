from crunevo.models import Post, PostComment, User
from crunevo.utils.feed import create_feed_item_for_all


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_anonymous_comment_blocked(client, db_session, test_user):
    post = Post(content="x", author=test_user)
    db_session.add(post)
    db_session.commit()
    create_feed_item_for_all("post", post.id)

    resp = client.post(f"/feed/comment/{post.id}", data={"body": "hi"})
    assert resp.status_code == 302
    assert PostComment.query.count() == 0


def test_admin_approves_comment(client, db_session, test_user):
    admin = User(
        username="adm",
        email="adm@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    post = Post(content="x", author=test_user)
    comment = PostComment(body="hello", post=post, pending=True)
    db_session.add_all([admin, post, comment])
    db_session.commit()

    login(client, "adm", "pass")
    resp = client.post(f"/admin/pending-comments/post/{comment.id}/approve")
    assert resp.status_code == 302
    assert PostComment.query.get(comment.id).pending is False
