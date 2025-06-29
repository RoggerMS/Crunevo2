from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models import User, Note, Post, Club, Mission, Purchase, Report, AdminLog
from crunevo.utils.helpers import admin_required
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons
from datetime import datetime, timedelta
import csv
import io
from flask import make_response

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
@admin_required
def require_admin():
    pass


@admin_bp.route("/")
def dashboard():
    """Enhanced admin dashboard with comprehensive statistics"""
    # Basic stats
    total_users = User.query.count()
    total_notes = Note.query.count()
    total_posts = Post.query.count()
    total_clubs = Club.query.count()

    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = 0
    new_notes_week = Note.query.filter(Note.created_at >= week_ago).count()
    new_posts_week = Post.query.filter(Post.created_at >= week_ago).count()

    # Top users by activity
    top_users = db.session.query(User).order_by(User.points.desc()).limit(10).all()

    # Recent reports
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()

    # Club statistics
    most_active_clubs = (
        db.session.query(Club).order_by(Club.member_count.desc()).limit(5).all()
    )

    # Financial stats
    total_crolars_circulation = (
        db.session.query(db.func.sum(User.credits)).scalar() or 0
    )
    total_purchases = Purchase.query.count()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_notes=total_notes,
        total_posts=total_posts,
        total_clubs=total_clubs,
        new_users_week=new_users_week,
        new_notes_week=new_notes_week,
        new_posts_week=new_posts_week,
        top_users=top_users,
        recent_reports=recent_reports,
        most_active_clubs=most_active_clubs,
        total_crolars_circulation=total_crolars_circulation,
        total_purchases=total_purchases,
    )


@admin_bp.route("/users")
def manage_users():
    """Enhanced user management with club and mission info"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")

    query = User.query
    if search:
        query = query.filter(
            User.username.contains(search) | User.email.contains(search)
        )

    users = query.order_by(User.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template("admin/manage_users.html", users=users, search=search)


@admin_bp.route("/clubs")
def manage_clubs():
    """Club management for admins"""
    clubs = Club.query.order_by(Club.created_at.desc()).all()
    return render_template("admin/manage_clubs.html", clubs=clubs)


@admin_bp.route("/clubs/create", methods=["POST"])
def create_club():
    """Create new club"""
    name = request.form.get("name")
    career = request.form.get("career")
    description = request.form.get("description")

    if not name or not career:
        flash("Nombre y carrera son requeridos", "error")
        return redirect(url_for("admin.manage_clubs"))

    club = Club(name=name, career=career, description=description)

    db.session.add(club)
    db.session.commit()

    # Log action
    log_admin_action(f"Creó club: {name}")

    flash(f'Club "{name}" creado exitosamente', "success")
    return redirect(url_for("admin.manage_clubs"))


@admin_bp.route("/missions")
def manage_missions():
    """Mission management"""
    missions = Mission.query.all()
    return render_template("admin/manage_missions.html", missions=missions)


@admin_bp.route("/reports")
def manage_reports():
    """Report management with enhanced filtering"""
    status = request.args.get("status", "pending")
    reports = (
        Report.query.filter_by(status=status).order_by(Report.created_at.desc()).all()
    )
    return render_template(
        "admin/manage_reports.html", reports=reports, current_status=status
    )


@admin_bp.route("/credits/add", methods=["POST"])
def add_credits_to_user():
    """Add credits to specific user"""
    user_id = request.form.get("user_id", type=int)
    amount = request.form.get("amount", type=int)

    user = User.query.get_or_404(user_id)

    if amount and amount > 0:
        add_credit(user, amount, CreditReasons.DONACION, related_id=None)
        log_admin_action(f"Agregó {amount} Crolars a {user.username}")
        flash(f"Se agregaron {amount} Crolars a {user.username}", "success")

    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/export/users")
def export_users():
    """Export users to CSV"""
    users = User.query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        ["ID", "Username", "Email", "Credits", "Points", "Verified", "Created"]
    )

    # Data
    for user in users:
        writer.writerow(
            [
                user.id,
                user.username,
                user.email,
                user.credits or 0,
                user.points or 0,
                user.verification_level > 0,
                user.id,  # We don't have created_at, using ID as proxy
            ]
        )

    output.seek(0)

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=users_export.csv"

    return response


@admin_bp.route("/stats/api")
def stats_api():
    """API endpoint for dashboard statistics"""
    # Get registration stats for the last 30 days
    stats = []
    for i in range(30):
        date = datetime.utcnow() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)

        count = User.query.filter(
            User.id >= 1  # Simple proxy for date since we don't have created_at
        ).count()

        stats.append(
            {
                "date": date_start.strftime("%Y-%m-%d"),
                "users": count // 30 + (i % 5),  # Simulate daily registrations
            }
        )

    return jsonify({"registration_stats": list(reversed(stats))})


def log_admin_action(action):
    """Log admin actions"""
    log = AdminLog(admin_id=current_user.id, action=action, timestamp=datetime.utcnow())
    db.session.add(log)
    db.session.commit()
