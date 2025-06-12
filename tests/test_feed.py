from crunevo.models import Note
from crunevo.utils.feed import create_feed_item_for_all


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password})


def test_feed_shows_note_for_other_user(client, db_session, test_user, another_user):
    note = Note(title="Feed note", author=test_user)
    db_session.add(note)
    db_session.commit()
    create_feed_item_for_all('apunte', note.id)

    login(client, another_user.username, 'secret')
    resp = client.get('/api/feed')
    assert resp.status_code == 200
    data = resp.get_json()[0]
    assert data['item_type'] == 'apunte'
    assert data['title'] == 'Feed note'

