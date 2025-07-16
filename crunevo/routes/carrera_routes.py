from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.user import User
from crunevo.models.post import Post
from crunevo.models.note import Note
from crunevo.models.course import Course
from crunevo.models.club import Club, ClubMember
from crunevo.models.event import Event
from crunevo.models.chat import Message
from crunevo.utils.helpers import activated_required, career_required
from datetime import datetime, timedelta
from sqlalchemy import or_

carrera_bp = Blueprint("carrera", __name__, url_prefix="/mi-carrera")


@carrera_bp.route("/")
@login_required
@activated_required
def index():
    """Main career center dashboard"""

    if current_user.role != "admin":
        flash("Acceso restringido", "warning")
        return redirect(url_for("feed.feed_home"))
    # Check if user has career assigned
    if not current_user.career:
        flash("Debes asignar una carrera para acceder a Mi Carrera", "warning")
        return redirect(url_for("auth.perfil"))

    # Get tab from query param
    tab = request.args.get("tab", "publicaciones")

    # Get career-specific stats
    career_stats = get_career_stats(current_user.career)

    return render_template(
        "carrera/index.html",
        tab=tab,
        career_stats=career_stats,
        user_career=current_user.career,
    )


@carrera_bp.route("/api/publicaciones")
@login_required
@career_required
def get_publicaciones():
    """Get career-specific posts"""
    if not current_user.career:
        return jsonify({"error": "No career assigned"}), 400

    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Get posts from users with same career
    posts = (
        Post.query.join(User)
        .filter(User.career == current_user.career)
        .order_by(Post.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    posts_data = []
    for post in posts.items:
        posts_data.append(
            {
                "id": post.id,
                "content": post.content,
                "author": {
                    "username": post.author.username,
                    "avatar_url": post.author.avatar_url,
                    "career": post.author.career,
                },
                "created_at": post.created_at.strftime("%d %b %Y, %H:%M"),
                "likes": post.likes,
                "comments_count": len(post.comments),
            }
        )

    return jsonify(
        {
            "posts": posts_data,
            "has_next": posts.has_next,
            "has_prev": posts.has_prev,
            "page": posts.page,
            "pages": posts.pages,
        }
    )


@carrera_bp.route("/api/apuntes")
@login_required
@career_required
def get_apuntes():
    """Get career-specific notes"""

    page = request.args.get("page", 1, type=int)
    course_filter = request.args.get("course", "")

    query = Note.query.join(User).filter(User.career == current_user.career)

    if course_filter:
        query = query.filter(Note.course.ilike(f"%{course_filter}%"))

    notes = query.order_by(Note.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )

    notes_data = []
    for note in notes.items:
        notes_data.append(
            {
                "id": note.id,
                "title": note.title,
                "description": note.description,
                "course": note.course,
                "tags": note.tags,
                "author": {
                    "username": note.author.username,
                    "avatar_url": note.author.avatar_url,
                },
                "views": note.views,
                "downloads": note.downloads,
                "created_at": note.created_at.strftime("%d %b %Y"),
            }
        )

    return jsonify(
        {"notes": notes_data, "has_next": notes.has_next, "has_prev": notes.has_prev}
    )


@carrera_bp.route("/api/cursos")
@login_required
@career_required
def get_cursos():
    """Get career-specific courses"""

    courses = (
        Course.query.filter(Course.category == current_user.career)
        .order_by(Course.views.desc())
        .limit(20)
        .all()
    )

    courses_data = []
    for course in courses:
        courses_data.append(
            {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "thumbnail_url": course.thumbnail_url,
                "creator": {"username": course.creator.username},
                "duration_minutes": course.duration_minutes,
                "difficulty": course.difficulty,
                "views": course.views,
            }
        )

    return jsonify({"courses": courses_data})


@carrera_bp.route("/api/clubes")
@login_required
def get_clubes():
    """Get career-specific clubs"""
    if not current_user.career:
        return jsonify({"error": "No career assigned"}), 400

    clubs = (
        Club.query.filter(Club.career == current_user.career)
        .order_by(Club.member_count.desc())
        .all()
    )

    clubs_data = []
    for club in clubs:
        # Check if user is member
        is_member = (
            ClubMember.query.filter_by(user_id=current_user.id, club_id=club.id).first()
            is not None
        )

        clubs_data.append(
            {
                "id": club.id,
                "name": club.name,
                "description": club.description,
                "avatar_url": club.avatar_url,
                "member_count": club.member_count,
                "is_member": is_member,
            }
        )

    return jsonify({"clubs": clubs_data})


@carrera_bp.route("/api/eventos")
@login_required
def get_eventos():
    """Get career-specific upcoming events"""
    if not current_user.career:
        return jsonify({"error": "No career assigned"}), 400

    # For now, get all upcoming events (can be filtered by category later)
    events = (
        Event.query.filter(
            Event.event_date >= datetime.utcnow(),
            or_(Event.category == current_user.career, Event.category == "general"),
        )
        .order_by(Event.event_date.asc())
        .limit(10)
        .all()
    )

    events_data = []
    for event in events:
        events_data.append(
            {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "event_date": event.event_date.strftime("%d %b %Y, %H:%M"),
                "image_url": event.image_url,
                "category": event.category,
                "is_upcoming": event.is_upcoming,
            }
        )

    return jsonify({"events": events_data})


@carrera_bp.route("/api/chat")
@login_required
def get_chat_messages():
    """Get career chat messages"""
    if not current_user.career:
        return jsonify({"error": "No career assigned"}), 400

        # Get recent messages for this career
        messages = (
            Message.query.join(User)
            .filter(
                User.career == current_user.career,
                Message.is_global.is_(True),
            )
            .order_by(Message.timestamp.desc())
            .limit(50)
            .all()
        )

    messages_data = []
    for msg in reversed(messages):  # Show oldest first
        messages_data.append(
            {
                "id": msg.id,
                "content": msg.content,
                "sender": {
                    "username": msg.sender.username,
                    "avatar_url": msg.sender.avatar_url,
                },
                "timestamp": msg.timestamp.strftime("%H:%M"),
            }
        )

    # Count active users in career chat (last 10 minutes)
    active_users = User.query.filter(
        User.career == current_user.career,
        User.id.in_(
            db.session.query(Message.sender_id)
            .filter(Message.timestamp >= datetime.utcnow() - timedelta(minutes=10))
            .distinct()
        ),
    ).count()

    return jsonify({"messages": messages_data, "active_users": active_users})


@carrera_bp.route("/api/chat", methods=["POST"])
@login_required
def send_chat_message():
    """Send message to career chat"""
    if not current_user.career:
        return jsonify({"error": "No career assigned"}), 400

    data = request.get_json()
    content = data.get("content", "").strip()

    if not content or len(content) > 500:
        return jsonify({"error": "Invalid message"}), 400

    message = Message(sender_id=current_user.id, content=content, is_global=True)

    db.session.add(message)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": {
                "id": message.id,
                "content": message.content,
                "sender": {
                    "username": current_user.username,
                    "avatar_url": current_user.avatar_url,
                },
                "timestamp": message.timestamp.strftime("%H:%M"),
            },
        }
    )


@carrera_bp.route("/api/destacados")
@login_required
def get_estudiantes_destacados():
    """Get featured students from same career"""
    if not current_user.career:
        return jsonify({"error": "No career assigned"}), 400

    # Get users with most activity in the career
    featured_users = (
        User.query.filter(
            User.career == current_user.career, User.id != current_user.id
        )
        .order_by(User.credits.desc(), User.points.desc())
        .limit(10)
        .all()
    )

    users_data = []
    for user in featured_users:
        # Calculate activity score
        notes_count = Note.query.filter_by(user_id=user.id).count()
        posts_count = Post.query.filter_by(author_id=user.id).count()

        users_data.append(
            {
                "id": user.id,
                "username": user.username,
                "avatar_url": user.avatar_url,
                "credits": user.credits,
                "points": user.points,
                "notes_count": notes_count,
                "posts_count": posts_count,
                "verification_level": user.verification_level,
            }
        )

    return jsonify({"users": users_data})


@carrera_bp.route("/api/join-club/<int:club_id>", methods=["POST"])
@login_required
def join_club(club_id):
    """Request to join a club"""
    club = Club.query.get_or_404(club_id)

    # Check if already member
    existing_member = ClubMember.query.filter_by(
        user_id=current_user.id, club_id=club_id
    ).first()

    if existing_member:
        return jsonify({"error": "Already a member"}), 400

    # Add as member
    member = ClubMember(user_id=current_user.id, club_id=club_id, role="member")

    club.member_count += 1

    db.session.add(member)
    db.session.commit()

    return jsonify({"success": True, "message": "Joined club successfully"})


def get_career_stats(career):
    """Get statistics for a career"""
    total_students = User.query.filter_by(career=career).count()
    total_notes = Note.query.join(User).filter(User.career == career).count()
    total_posts = Post.query.join(User).filter(User.career == career).count()
    total_clubs = Club.query.filter_by(career=career).count()

    return {
        "total_students": total_students,
        "total_notes": total_notes,
        "total_posts": total_posts,
        "total_clubs": total_clubs,
    }
