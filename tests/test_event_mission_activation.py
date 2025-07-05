from datetime import datetime, timedelta
from crunevo.models import Event, Mission
from crunevo.routes.missions_routes import compute_mission_states


def test_event_mission_activation(db_session, test_user):
    event = Event(title="MDay", event_date=datetime.utcnow() + timedelta(days=3))
    db_session.add(event)
    db_session.flush()
    mission = Mission(
        code="event_mission",
        description="Linked",
        goal=1,
        credit_reward=1,
        event_id=event.id,
        is_active=False,
    )
    db_session.add(mission)
    db_session.commit()

    compute_mission_states(test_user)
    db_session.refresh(mission)
    assert mission.is_active is True
