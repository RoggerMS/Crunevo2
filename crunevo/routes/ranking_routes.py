from flask import Blueprint, render_template
from crunevo.models import RankingCache
from datetime import datetime

ranking_bp = Blueprint("ranking", __name__, url_prefix="/ranking")


@ranking_bp.route("/")
def show_ranking():
    top = (
        RankingCache.query.filter_by(period="semanal")
        .order_by(RankingCache.score.desc())
        .limit(10)
        .all()
    )
    last_update = top[0].calculated_at if top else None
    return render_template(
        "ranking/index.html",
        ranking=top,
        now=datetime.utcnow(),
        last_update=last_update,
    )
