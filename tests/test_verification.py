from crunevo.models import User


def test_badge_visible(client, db_session):
    user = User(
        username="v",
        email="v@example.com",
        activated=True,
        avatar_url="a",
        verification_level=2,
    )
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "v", "password": "StrongPassw0rd!"})
    resp = client.get("/")
    assert b"bi-mortarboard-fill" in resp.data


def test_badge_hidden(client, db_session):
    user = User(username="n", email="n@example.com", activated=True, avatar_url="a")
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    client.post("/login", data={"username": "n", "password": "StrongPassw0rd!"})
    resp = client.get("/")
    assert b"bi-mortarboard-fill" not in resp.data
