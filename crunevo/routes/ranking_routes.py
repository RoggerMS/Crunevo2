from datetime import datetime, timedelta
from flask import Blueprint, render_template, request
from sqlalchemy import func, desc
from crunevo.extensions import db
from crunevo.models import User, Credit

ranking_bp = Blueprint("ranking", __name__, url_prefix="/ranking")


@ranking_bp.route("/")
def show_ranking():
    range_opt = request.args.get("range", "week")
    now = datetime.utcnow()
    if range_opt == "week":
        start = now - timedelta(days=7)
    elif range_opt == "month":
        start = now - timedelta(days=30)
    else:
        start = None

    query = db.session.query(
        User,
        func.coalesce(func.sum(Credit.amount), 0).label("total"),
    ).outerjoin(Credit)
    if start:
        query = query.filter(Credit.timestamp >= start)
    ranking = query.group_by(User.id).order_by(desc("total")).limit(10).all()

    return render_template(
        "ranking/index.html",
        ranking=ranking,
        range=range_opt,
    )
