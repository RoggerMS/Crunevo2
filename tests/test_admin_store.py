from crunevo.models import User, Product


def test_admin_delete_product(client, db_session):
    admin = User(
        username="adm",
        email="adm@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    product = Product(name="prod", price=1, stock=1)
    db_session.add_all([admin, product])
    db_session.commit()

    client.post("/login", data={"username": "adm", "password": "pass"})
    resp = client.post(f"/admin/products/{product.id}/delete")
    assert resp.status_code == 302
    assert Product.query.get(product.id) is None
