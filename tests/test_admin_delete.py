from crunevo.models import User, Post, Note
from crunevo.utils.feed import create_feed_item_for_all


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_admin_delete_post(client, db_session, test_user):
    admin = User(
        username="adm",
        email="adm@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    post = Post(content="x", author=test_user)
    db_session.add_all([admin, post])
    db_session.commit()
    create_feed_item_for_all("post", post.id)
    login(client, "adm", "pass")
    resp = client.post(f"/admin/delete-post/{post.id}")
    assert resp.status_code == 302
    assert Post.query.get(post.id) is None


def test_admin_delete_note(client, db_session, test_user):
    admin = User(
        username="adm2",
        email="adm2@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    note = Note(title="t", filename="file.pdf", author=test_user)
    db_session.add_all([admin, note])
    db_session.commit()
    create_feed_item_for_all("apunte", note.id)
    login(client, "adm2", "pass")
    resp = client.post(f"/admin/delete-note/{note.id}")
    assert resp.status_code == 302
    assert Note.query.get(note.id) is None
