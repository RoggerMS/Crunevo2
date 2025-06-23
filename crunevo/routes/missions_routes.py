from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import current_user
from sqlalchemy import func
from crunevo.models import Mission, UserMission, Note, PostComment, Post
from crunevo.extensions import db
from crunevo.utils.credits import add_credit
from crunevo.constants import CreditReasons

missions_bp = Blueprint("missions", __name__, url_prefix="/misiones")


@missions_bp.route("/")
def list_missions():
    if not current_user.is_authenticated:
        return render_template("misiones/index.html", missions=[])

    one_week_ago = datetime.utcnow() - timedelta(days=7)

    # Ensure default missions exist
    defaults = [
        {
            "code": "upload_note",
            "description": "Subir 1 apunte esta semana",
            "goal": 1,
            "credit_reward": 5,
        },
        {
            "code": "comment_posts",
            "description": "Comentar en 3 publicaciones",
            "goal": 3,
            "credit_reward": 3,
        },
        {
            "code": "receive_likes",
            "description": "Recibir 5 likes en tus publicaciones",
            "goal": 5,
            "credit_reward": 3,
        },
    ]
    for d in defaults:
        if not Mission.query.filter_by(code=d["code"]).first():
            db.session.add(Mission(**d))
    db.session.commit()

    missions = Mission.query.all()
    mission_states = []
    for m in missions:
        progress = 0
        if m.code == "upload_note":
            progress = (
                Note.query.filter_by(user_id=current_user.id)
                .filter(Note.created_at >= one_week_ago)
                .count()
            )
        elif m.code == "comment_posts":
            progress = (
                PostComment.query.filter_by(author_id=current_user.id)
                .filter(PostComment.timestamp >= one_week_ago)
                .count()
            )
        elif m.code == "receive_likes":
            progress = (
                db.session.query(func.coalesce(func.sum(Post.likes), 0))
                .filter_by(author_id=current_user.id)
                .scalar()
                or 0
            )
        completed = progress >= m.goal
        record = UserMission.query.filter_by(
            user_id=current_user.id, mission_id=m.id
        ).first()
        if completed and not record:
            db.session.add(UserMission(user_id=current_user.id, mission_id=m.id))
            add_credit(current_user, m.credit_reward, CreditReasons.DONACION)
            db.session.commit()
        mission_states.append(
            {
                "mission": m,
                "progress": progress,
                "completed": completed or record is not None,
            }
        )
    return render_template("misiones/index.html", missions=mission_states)
