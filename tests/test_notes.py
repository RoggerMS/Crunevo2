from crunevo.models import Note, FeedItem
from crunevo.utils.feed import create_feed_item_for_all


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_delete_own_note(client, db_session, test_user):
    note = Note(title="n", filename="file.pdf", author=test_user)
    db_session.add(note)
    db_session.commit()
    create_feed_item_for_all("apunte", note.id)

    login(client, test_user.username, "secret")
    resp = client.post(f"/notes/delete/{note.id}")
    assert resp.status_code == 302
    assert Note.query.get(note.id) is None
    assert not any(i.get("ref_id") == note.id for i in FeedItem.query.all())


def test_delete_note_forbidden(client, db_session, test_user, another_user):
    note = Note(title="n", filename="file.pdf", author=test_user)
    db_session.add(note)
    db_session.commit()
    create_feed_item_for_all("apunte", note.id)

    login(client, another_user.username, "secret")
    resp = client.post(f"/notes/delete/{note.id}")
    assert resp.status_code == 403
    assert Note.query.get(note.id) is not None


def test_notes_page_loads(client, db_session, test_user):
    note = Note(title="n", filename="file.pdf", author=test_user)
    db_session.add(note)
    db_session.commit()
    login(client, test_user.username, "secret")
    resp = client.get("/notes/")
    assert resp.status_code == 200
    assert b"notesList" in resp.data
