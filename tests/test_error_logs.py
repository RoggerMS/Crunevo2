from crunevo.models import User, SystemErrorLog


def test_error_logging_and_resolve(client, db_session):
    admin = User(
        username="adm",
        email="adm@example.com",
        role="admin",
        activated=True,
        avatar_url="a",
    )
    admin.set_password("pass")
    db_session.add(admin)
    db_session.commit()

    @client.application.route("/boom")
    def boom():
        raise RuntimeError("boom")

    resp = client.get("/boom")
    assert resp.status_code == 500
    log = SystemErrorLog.query.first()
    assert log and log.ruta == "/boom"

    client.post("/login", data={"username": "adm", "password": "pass"})
    resp = client.post(f"/admin/errores/{log.id}/resolver")
    assert resp.status_code == 302
    assert SystemErrorLog.query.get(log.id).resuelto is True
