from datetime import datetime, timedelta
from crunevo.utils.scoring import compute_score
import pytest


def test_score_formula():
    now = datetime.utcnow()
    assert compute_score(0, 0, 0, now) == 0
    high = compute_score(2, 1, 1, now)
    assert high == pytest.approx(2 * 4 + 1 * 2 + 1, rel=1e-6)
    old = compute_score(2, 1, 1, now - timedelta(hours=50))
    assert old == 0
