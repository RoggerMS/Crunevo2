from datetime import datetime
from crunevo.models import Event


def test_calendar_json(client, db_session):
    event = Event(title="Test", event_date=datetime.utcnow())
    db_session.add(event)
    db_session.commit()
    resp = client.get("/eventos/calendario")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]["title"] == "Test"
    assert "start" in data[0]
