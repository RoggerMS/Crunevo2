from datetime import datetime, timedelta
from types import SimpleNamespace

from crunevo.jobs import decay


class FakeFeedItem:
    def __init__(self, i):
        self.id = i
        self.ref_id = i
        self.owner_id = 1
        self.item_type = "apunte"
        self.score = 0
        self.created_at = datetime.utcnow() - timedelta(hours=2)

    def to_dict(self):
        return {"id": self.id}


class FakeQuery:
    def __init__(self, items):
        self.items = items

    def filter(self, *a, **k):
        return self

    def order_by(self, *a):
        return self

    def offset(self, val):
        self.off = val
        return self

    def limit(self, val):
        self.lim = val
        return self

    def all(self):
        return self.items[self.off : self.off + self.lim]


def test_decay_batches(monkeypatch):
    items = [FakeFeedItem(i) for i in range(1500)]
    q = FakeQuery(items)

    class DummyAttr:
        def __le__(self, other):
            return True

        def __eq__(self, other):
            return True

    class DummyFeedItem:
        item_type = DummyAttr()
        created_at = DummyAttr()
        query = q

    monkeypatch.setattr(decay, "FeedItem", DummyFeedItem)
    monkeypatch.setattr(decay, "compute_score", lambda *a, **k: 0)
    monkeypatch.setattr(
        decay,
        "Note",
        SimpleNamespace(
            query=SimpleNamespace(
                get=lambda i: SimpleNamespace(
                    likes=0,
                    downloads=0,
                    comments_count=0,
                    created_at=datetime.utcnow() - timedelta(hours=2),
                )
            )
        ),
    )
    commits = []
    monkeypatch.setattr(decay.db.session, "commit", lambda: commits.append(True))
    monkeypatch.setattr(decay, "push_items", lambda *a, **k: None)

    decay.decay_scores(batch_size=1000)
    assert len(commits) == 2
