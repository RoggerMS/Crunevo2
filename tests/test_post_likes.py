from crunevo.models import Post, PostReaction


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_like_post_handles_null_likes(client, db_session, test_user, another_user):
    post = Post(content="hello", author=another_user)
    db_session.add(post)
    db_session.commit()

    login(client, test_user.username, "secret")
    resp = client.post(f"/feed/like/{post.id}", data={"reaction": "🔥"})
    assert resp.status_code == 200
    assert resp.get_json()["counts"]["🔥"] == 1

    assert PostReaction.query.count() == 1


def test_change_reaction(client, db_session, test_user, another_user):
    post = Post(content="hi", author=another_user)
    db_session.add(post)
    db_session.commit()

    login(client, test_user.username, "secret")
    client.post(f"/feed/like/{post.id}", data={"reaction": "🔥"})
    client.post(f"/feed/like/{post.id}", data={"reaction": "😂"})

    reaction = PostReaction.query.filter_by(
        user_id=test_user.id, post_id=post.id
    ).first()
    assert reaction.reaction_type == "😂"


def test_remove_reaction(client, db_session, test_user, another_user):
    post = Post(content="bye", author=another_user)
    db_session.add(post)
    db_session.commit()

    login(client, test_user.username, "secret")
    client.post(f"/feed/like/{post.id}", data={"reaction": "🔥"})
    resp = client.post(f"/feed/like/{post.id}", data={"reaction": "🔥"})
    assert resp.get_json()["counts"] == {}
    assert PostReaction.query.count() == 0
