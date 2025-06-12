from datetime import datetime, timedelta
from crunevo.utils.scoring import compute_score
import pytest


def test_score_formula(app):
    now = datetime.utcnow()
    with app.app_context():
        assert compute_score(0, 0, 0, now) == 0
        base = compute_score(2, 1, 1, now)
        weights = (
            app.config["FEED_LIKE_W"],
            app.config["FEED_DL_W"],
            app.config["FEED_COM_W"],
        )
        assert base == pytest.approx(
            2 * weights[0] + 1 * weights[1] + weights[2], rel=1e-6
        )

        baseline = compute_score(1, 0, 0, now)
        app.config["FEED_LIKE_W"] = 10
        boosted = compute_score(1, 0, 0, now)
        assert boosted > baseline

        very_old = compute_score(50, 50, 10, now - timedelta(days=10))
        assert very_old > 0
