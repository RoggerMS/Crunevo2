from crunevo.models import Note, Post, Report
from crunevo.constants import NOTE_CATEGORIES


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_edit_note(client, db_session, test_user):
    note = Note(title="t", filename="file.pdf", author=test_user)
    db_session.add(note)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.post(
        f"/notes/edit/{note.id}",
        data={
            "title": "Nuevo",
            "description": "d",
            "category": NOTE_CATEGORIES[0],
            "tags": "x",
        },
    )
    assert resp.status_code == 302
    db_session.refresh(note)
    assert note.title == "Nuevo"


def test_report_post(client, db_session, test_user, another_user):
    post = Post(content="bad", author=test_user)
    db_session.add(post)
    db_session.commit()

    login(client, another_user.username, "secret")
    resp = client.post(f"/feed/post/reportar/{post.id}", data={"reason": "spam"})
    assert resp.status_code == 302
    assert Report.query.filter_by(user_id=another_user.id).count() == 1
