from datetime import date, timedelta
from crunevo.utils.login_history import record_login
from crunevo.constants import CreditReasons


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_streak_claim(db_session, client, test_user):
    record_login(test_user, date.today())
    login(client, test_user.username)
    resp = client.post("/api/reclamar-racha")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]
    assert data["credits"] == 2
    assert test_user.credits == 2
    assert test_user.credit_history[-1].reason == CreditReasons.RACHA_LOGIN


def test_streak_resets_after_break(db_session, client, test_user):
    start = date.today() - timedelta(days=2)
    record_login(test_user, start)
    record_login(test_user, start + timedelta(days=1))
    record_login(test_user, start + timedelta(days=3))
    login(client, test_user.username)
    resp = client.post("/api/reclamar-racha")
    assert resp.status_code == 200
    assert test_user.login_streak.current_day == 1


def test_streak_device_token_block(db_session, client, test_user, another_user):
    token = "abc123"
    record_login(test_user, date.today())
    login(client, test_user.username)
    resp1 = client.post("/api/reclamar-racha", headers={"X-Device-Token": token})
    assert resp1.status_code == 200

    record_login(another_user, date.today())
    login(client, another_user.username)
    resp2 = client.post("/api/reclamar-racha", headers={"X-Device-Token": token})
    assert resp2.status_code == 400
