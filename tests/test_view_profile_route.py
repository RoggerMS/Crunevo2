from crunevo.models import User


def create_user(username, email):
    user = User(username=username, email=email, activated=True, avatar_url="a")
    user.set_password("pass")
    return user


def test_view_profile_existing_user(client, db_session):
    user = create_user("alice", "alice@example.com")
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "alice", "password": "pass"})
    resp = client.get("/perfil/alice")
    assert resp.status_code == 200


def test_view_profile_not_found(client, db_session, caplog):
    viewer = create_user("bob", "bob@example.com")
    db_session.add(viewer)
    db_session.commit()
    client.post("/login", data={"username": "bob", "password": "pass"})
    with caplog.at_level("WARNING"):
        resp = client.get("/perfil/missing")
    assert resp.status_code == 404
    assert "User missing not found" in caplog.text


def test_view_profile_null_verification_level(client, db_session):
    user = create_user("charlie", "charlie@example.com")
    user.verification_level = None
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "charlie", "password": "pass"})
    resp = client.get("/perfil/charlie")
    assert resp.status_code == 200
