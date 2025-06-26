from crunevo.models import Post


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_like_post_handles_null_likes(client, db_session, test_user, another_user):
    post = Post(content="hello", author=another_user, likes=None)
    db_session.add(post)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.post(f"/like/{post.id}")
    assert resp.status_code == 200
    assert resp.get_json()["likes"] == 1

    db_session.refresh(post)
    assert post.likes == 1
