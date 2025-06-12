from datetime import datetime, timedelta
from crunevo.extensions import db
from crunevo.models import User, Note, Credit, RankingCache
from crunevo.utils import unlock_achievement
from crunevo.constants import AchievementCodes


def calculate_weekly_ranking():
    """Compute and store the weekly ranking for all users."""
    start_date = datetime.utcnow() - timedelta(days=7)
    db.session.query(RankingCache).filter_by(period='semanal').delete()

    users = User.query.all()
    created = []
    for user in users:
        apuntes = (
            Note.query.filter(Note.author == user, Note.created_at >= start_date)
            .count()
        )
        votos = sum(
            getattr(n, "votes", getattr(n, "likes", 0))
            for n in Note.query.filter(
                Note.author == user, Note.created_at >= start_date
            ).all()
        )  # usa n.votes o n.likes si existen
        # Respuestas útiles en el foro (a implementar cuando el foro esté listo)
        respuestas = 0
        creditos = sum(
            float(c.amount)
            for c in getattr(user, "credit_history", [])  # puede estar vacío
            if c.timestamp >= start_date and c.amount > 0
        )

        score = int((5 * apuntes) + (2 * respuestas) + (1 * votos) + (10 * creditos))
        if score > 0:
            rc = RankingCache(user_id=user.id, score=score, period='semanal')
            db.session.add(rc)
            created.append(rc)

    db.session.commit()

    ranked = sorted(created, key=lambda r: r.score, reverse=True)
    for rc in ranked[:3]:
        unlock_achievement(rc.user, AchievementCodes.TOP_3)
