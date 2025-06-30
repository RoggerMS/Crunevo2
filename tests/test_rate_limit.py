from crunevo.models import User


def test_login_rate_limit(client):
    for _ in range(5):
        client.post("/login", data={"username": "none", "password": "wrong"})
    resp = client.post("/login", data={"username": "none", "password": "wrong"})
    assert resp.status_code == 200
    assert "Has excedido el número de intentos" in resp.get_data(as_text=True)


def test_register_rate_limit(client):
    for i in range(15):
        client.post(
            "/onboarding/register",
            data={"email": f"a{i}@ex.com", "password": "StrongPassw0rd!"},
        )
    resp = client.post(
        "/onboarding/register",
        data={"email": "x@ex.com", "password": "StrongPassw0rd!"},
    )
    assert resp.status_code == 429


def test_resend_rate_limit(client, db_session):
    user = User(username="rate", email="rate@example.com")
    user.set_password("StrongPassw0rd!")
    db_session.add(user)
    db_session.commit()
    client.post(
        "/login",
        data={"username": user.username, "password": "StrongPassw0rd!"},
    )
    from unittest.mock import patch

    with patch("crunevo.routes.onboarding_routes.send_confirmation_email"):
        for _ in range(3):
            client.post("/onboarding/resend")
        resp = client.post("/onboarding/resend")
    assert resp.status_code == 429
