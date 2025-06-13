from bs4 import BeautifulSoup
from crunevo.models import User


def test_login_csrf(app, db_session):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    user = User(username="csrf", email="c@example.com", activated=True)
    user.set_password("secret")
    db_session.add(user)
    db_session.commit()
    resp = client.get("/login")
    soup = BeautifulSoup(resp.data, "html.parser")
    token = soup.find("input", {"name": "csrf_token"})["value"]
    resp = client.post(
        "/login",
        data={"username": user.username, "password": "secret", "csrf_token": token},
    )
    assert resp.status_code == 302
