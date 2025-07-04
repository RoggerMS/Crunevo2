from crunevo.models import TwoFactorToken
import pyotp


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_twofactor_setup_and_verify(client, db_session, test_user):
    login(client, test_user.username)
    client.get("/2fa/setup")
    token = TwoFactorToken.query.filter_by(user_id=test_user.id).first()
    assert token is not None
    code = pyotp.TOTP(token.secret).now()
    client.post("/2fa/setup", data={"code": code})
    db_session.refresh(token)
    assert token.confirmed_at is not None
    assert token.backup_codes


def test_login_twofactor_flow(client, db_session, test_user):
    login(client, test_user.username)
    client.get("/2fa/setup")
    token = TwoFactorToken.query.filter_by(user_id=test_user.id).first()
    code = pyotp.TOTP(token.secret).now()
    client.post("/2fa/setup", data={"code": code})
    client.get("/logout")

    resp = login(client, test_user.username)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login/verify")

    backup = token.backup_codes.split(",")[0]
    resp = client.post("/login/verify", data={"code": backup})
    assert resp.status_code == 302
    db_session.refresh(token)
    assert backup not in token.backup_codes
