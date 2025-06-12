from crunevo.models import Note


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password})


def test_like_adds_credit_and_counts(client, db_session, test_user, another_user):
    note = Note(title="test", author=another_user)
    db_session.add(note)
    db_session.commit()

    login(client, 'tester', 'secret')
    resp = client.post(f'/notes/{note.id}/like')
    assert resp.status_code == 200
    assert resp.get_json()['likes'] == 1

    db_session.refresh(note)
    db_session.refresh(another_user)
    assert note.likes == 1
    assert another_user.credits == 1


def test_cannot_like_own_note(client, db_session, test_user):
    note = Note(title="self", author=test_user)
    db_session.add(note)
    db_session.commit()

    login(client, 'tester', 'secret')
    resp = client.post(f'/notes/{note.id}/like')
    assert resp.status_code == 403

    db_session.refresh(note)
    assert note.likes == 0


def test_user_cannot_vote_twice(client, db_session, test_user, another_user):
    note = Note(title="Test note", author=another_user)
    db_session.add(note)
    db_session.commit()

    login(client, 'tester', 'secret')
    resp1 = client.post(f'/notes/{note.id}/like')
    assert resp1.status_code == 200

    resp2 = client.post(f'/notes/{note.id}/like')
    assert resp2.status_code == 400

    db_session.refresh(note)
    assert note.likes == 1
