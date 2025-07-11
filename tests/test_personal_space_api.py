from crunevo.models import PersonalBlock, User


def login(client, username, password="secret"):
    return client.post("/login", data={"username": username, "password": password})


def create_inactive_user(db_session):
    user = User(
        username="inactive",
        email="inactive@example.com",
        activated=False,
        avatar_url="a",
    )
    user.set_password("secret")
    db_session.add(user)
    db_session.commit()
    return user


def test_create_block_requires_login(client):
    resp = client.post("/espacio-personal/api/blocks", json={"block_type": "nota"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_create_block_requires_activation(client, db_session):
    user = create_inactive_user(db_session)
    login(client, user.username)
    resp = client.post("/espacio-personal/api/blocks", json={"block_type": "nota"})
    assert resp.status_code == 302
    assert "/onboarding/pending" in resp.headers["Location"]


def test_create_block_success(client, db_session, test_user):
    login(client, test_user.username)
    resp = client.post(
        "/espacio-personal/api/blocks",
        json={"block_type": "nota", "title": "My Note"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["block"]["title"] == "My Note"
    assert PersonalBlock.query.filter_by(user_id=test_user.id).count() == 1


def test_update_block(client, db_session, test_user, another_user):
    block = PersonalBlock(user_id=test_user.id, block_type="nota", title="Old")
    db_session.add(block)
    db_session.commit()

    login(client, test_user.username)
    resp = client.put(
        f"/espacio-personal/api/blocks/{block.id}",
        json={"title": "New"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["block"]["title"] == "New"
    db_session.refresh(block)
    assert block.title == "New"

    login(client, another_user.username)
    resp2 = client.put(
        f"/espacio-personal/api/blocks/{block.id}",
        json={"title": "Bad"},
    )
    assert resp2.status_code == 404


def test_delete_block(client, db_session, test_user, another_user):
    block = PersonalBlock(user_id=test_user.id, block_type="nota")
    db_session.add(block)
    db_session.commit()

    login(client, test_user.username)
    resp = client.delete(f"/espacio-personal/api/blocks/{block.id}")
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    assert PersonalBlock.query.get(block.id) is None

    block2 = PersonalBlock(user_id=test_user.id, block_type="nota")
    db_session.add(block2)
    db_session.commit()
    login(client, another_user.username)
    resp2 = client.delete(f"/espacio-personal/api/blocks/{block2.id}")
    assert resp2.status_code == 404


def test_reorder_blocks(client, db_session, test_user):
    b1 = PersonalBlock(user_id=test_user.id, block_type="nota", order_position=1)
    b2 = PersonalBlock(user_id=test_user.id, block_type="nota", order_position=2)
    db_session.add_all([b1, b2])
    db_session.commit()

    login(client, test_user.username)
    resp = client.post(
        "/espacio-personal/api/blocks/reorder",
        json={"blocks": [{"id": b2.id, "position": 1}, {"id": b1.id, "position": 2}]},
    )
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    db_session.refresh(b1)
    db_session.refresh(b2)
    assert b2.order_position == 1
    assert b1.order_position == 2

    resp2 = client.post(
        "/espacio-personal/api/blocks/reorder",
        json={},
    )
    assert resp2.status_code == 200
