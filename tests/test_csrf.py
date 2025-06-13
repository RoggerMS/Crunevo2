from bs4 import BeautifulSoup
from pathlib import Path
import re


def test_login_csrf(app, db_session, client, test_user):
    app.config["WTF_CSRF_ENABLED"] = True
    resp = client.get("/login")
    soup = BeautifulSoup(resp.data, "html.parser")
    token = soup.find("input", {"name": "csrf_token"})["value"]
    resp = client.post(
        "/login",
        data={
            "username": test_user.username,
            "password": "secret",
            "csrf_token": token,
        },
    )
    assert resp.status_code == 302


def test_post_forms_have_csrf_macro():
    pattern = re.compile(r'<form[^>]*method=["\']post["\'][^>]*>', re.IGNORECASE)
    missing = []
    for path in Path("crunevo/templates").rglob("*.html"):
        text = path.read_text()
        if pattern.search(text) and "{{ csrf.csrf_field() }}" not in text:
            missing.append(str(path))
    assert not missing, "Missing csrf_field in: " + ", ".join(missing)
