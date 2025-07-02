from crunevo.models import Post, Note


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_delete_account(client, db_session, test_user):
    post = Post(content="bye", author=test_user)
    note = Note(title="n", filename="n.pdf", author=test_user)
    db_session.add_all([post, note])
    db_session.commit()

    login(client, test_user.username)
    resp = client.post("/perfil/eliminar-cuenta")
    assert resp.status_code == 302
    db_session.refresh(test_user)
    assert not test_user.activated
    assert Post.query.get(post.id) is None
    assert Note.query.get(note.id) is None
