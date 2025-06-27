from crunevo.models import Mission, Note, UserMission


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_claim_mission(client, db_session, test_user):
    mission = Mission(
        code="subir_apuntes_1",
        description="Sube 1 apunte",
        goal=1,
        credit_reward=5,
    )
    db_session.add(mission)
    db_session.commit()

    note = Note(title="n", filename="f.pdf", author=test_user)
    db_session.add(note)
    db_session.commit()

    login(client, test_user.username)
    resp = client.post(f"/misiones/reclamar_mision/{mission.id}")
    assert resp.status_code == 302
    db_session.refresh(test_user)
    assert test_user.credits == 5
    assert (
        UserMission.query.filter_by(user_id=test_user.id, mission_id=mission.id).count()
        == 1
    )

    # Second claim should do nothing
    resp2 = client.post(f"/misiones/reclamar_mision/{mission.id}")
    assert resp2.status_code == 302
    db_session.refresh(test_user)
    assert test_user.credits == 5
    assert (
        UserMission.query.filter_by(user_id=test_user.id, mission_id=mission.id).count()
        == 1
    )
