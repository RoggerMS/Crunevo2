import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crunevo.app import create_app
from crunevo.extensions import db, mail
from crunevo.models import User
from crunevo.cache import feed_cache
import fakeredis


@pytest.fixture
def app():
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    app = create_app()
    app.config["TESTING"] = True
    app.config["MAIL_SUPPRESS_SEND"] = True
    mail.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    return db.session


@pytest.fixture
def test_user(db_session):
    user = User(username="tester", email="tester@example.com", activated=True, avatar_url="a")
    user.set_password("secret")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def another_user(db_session):
    user = User(username="tester2", email="tester2@example.com", activated=True, avatar_url="a")
    user.set_password("secret")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    r = fakeredis.FakeRedis()
    monkeypatch.setattr(feed_cache, "r", r)
    yield r
