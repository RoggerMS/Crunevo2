import pytest


def login(client, username, password="secret"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_personal_space_views(client, test_user):
    pytest.skip("personal space views require additional setup")


def test_apply_template_by_slug(client, test_user):
    login(client, test_user.username)
    resp = client.post(
        "/personal-space/templates/aplicar/university-student",
        environ_overrides={"wsgi.url_scheme": "https"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"]


def test_dashboard_view(client, test_user):
    login(client, test_user.username)
    resp = client.get(
        "/personal-space/",
        environ_overrides={"wsgi.url_scheme": "https"},
    )
    assert resp.status_code == 200


def test_analytics_dashboard_view(client, test_user):
    login(client, test_user.username)
    resp = client.get(
        "/personal-space/analytics",
        environ_overrides={"wsgi.url_scheme": "https"},
    )
    assert resp.status_code == 200
