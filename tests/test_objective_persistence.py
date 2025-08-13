from flask import template_rendered
from crunevo.models.personal_space_block import PersonalSpaceBlock


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def test_objective_view_uses_template(client, app, db_session, test_user):
    block = PersonalSpaceBlock(user_id=test_user.id, type="objetivo", title="Obj")
    db_session.add(block)
    db_session.commit()

    recorded = []

    def record(sender, template, context, **extra):
        recorded.append(template.name)

    template_rendered.connect(record, app)
    login(client, test_user.username)
    resp = client.get(
        f"/personal-space/block/{block.id}",
        environ_overrides={"wsgi.url_scheme": "https"},
    )
    template_rendered.disconnect(record, app)

    assert resp.status_code == 200
    assert "personal_space/views/objective_detail.html" in recorded


def test_patch_objective_persists(client, db_session, test_user):
    block = PersonalSpaceBlock(user_id=test_user.id, type="objetivo", title="Obj")
    db_session.add(block)
    db_session.commit()

    login(client, test_user.username)
    resp = client.patch(
        f"/api/personal-space/objectives/{block.id}",
        json={"title": "Nuevo"},
        environ_overrides={"wsgi.url_scheme": "https"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["objective"]["title"] == "Nuevo"
    db_session.refresh(block)
    assert block.get_metadata().get("objective", {}).get("title") == "Nuevo"
