from datetime import datetime, timedelta
from flask import Blueprint, render_template, request
from sqlalchemy import func, desc
from sqlalchemy.exc import ProgrammingError, OperationalError
from crunevo.extensions import db
from crunevo.models import User, Credit, Referral

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


# Backwards compatibility alias
ranking_bp.add_url_rule("/", endpoint="index", view_func=show_ranking)


@ranking_bp.route("/referidos")
def top_referrers():
    now = datetime.utcnow()
    start = now - timedelta(days=30)
    try:
        ranking = (
            db.session.query(
                User,
                func.count(Referral.id).label("total"),
            )
            .join(Referral, Referral.invitador_id == User.id)
            .filter(Referral.completado.is_(True))
            .filter(Referral.fecha_creacion >= start)
            .group_by(User.id)
            .order_by(desc("total"))
            .limit(10)
            .all()
        )
    except (ProgrammingError, OperationalError):
        db.session.rollback()
        ranking = []

    return render_template("ranking/top_referrals.html", ranking=ranking)
