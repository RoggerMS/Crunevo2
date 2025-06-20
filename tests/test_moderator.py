from crunevo.models import User, Product


def test_moderator_read_only(client, db_session):
    mod = User(
        username="mod",
        email="mod@example.com",
        role="moderator",
        activated=True,
        avatar_url="a",
    )
    mod.set_password("pass")
    db_session.add(mod)
    db_session.commit()
    client.post("/login", data={"username": "mod", "password": "pass"})

    resp = client.get("/admin/store")
    assert resp.status_code == 200

    resp = client.post(
        "/admin/products/new",
        data={"name": "p", "price": 1, "stock": 1},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert Product.query.count() == 0

    resp = client.post("/admin/users", data={"user_id": 1})
    assert resp.status_code == 403
