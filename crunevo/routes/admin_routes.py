import os
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_required
from crunevo.utils.helpers import activated_required, admin_required
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from datetime import datetime
from crunevo.models import User, Product, Report, Note, Credit
from crunevo.utils.ranking import calculate_weekly_ranking
from crunevo.utils.audit import record_auth_event
import cloudinary.uploader

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
@admin_required
def before_admin():
    pass


@admin_bp.route("/")
@activated_required
def dashboard():
    stats = {
        "users_total": User.query.count(),
        "notes_today": Note.query.filter(
            Note.created_at >= datetime.utcnow().date()
        ).count(),
        "credits_today": db.session.query(db.func.sum(Credit.amount))
        .filter(Credit.timestamp >= datetime.utcnow().date())
        .scalar()
        or 0,
    }

    uploads_chart_data = {
        "labels": [],
        "datasets": [
            {
                "label": "Subidas",
                "data": [],
                "borderColor": "#7b3aed",
            }
        ],
    }
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        uploads_chart_data=uploads_chart_data,
    )


@admin_bp.route("/users", methods=["GET", "POST"])
@activated_required
def manage_users():
    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        user = User.query.get_or_404(user_id)
        user.role = request.form.get("role", user.role)
        user.activated = "active" in request.form
        credits_delta = request.form.get("credits", type=int)
        if credits_delta:
            credit = Credit(
                user_id=user.id, amount=credits_delta, reason="admin_adjust"
            )
            db.session.add(credit)
            user.credits += credits_delta
        db.session.commit()
        flash("Usuario actualizado")
        return redirect(url_for("admin.manage_users"))
    users = User.query.all()
    return render_template("admin/manage_users.html", users=users)


@admin_bp.route("/store", methods=["GET", "POST"])
@activated_required
def manage_store():
    products = Product.query.all()
    return render_template("admin/manage_store.html", products=products)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@activated_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description")
        price = request.form["price"]
        stock = request.form.get("stock", 0)
        file = request.files.get("image")
        image_url = None
        if file and file.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                res = cloudinary.uploader.upload(file)
                image_url = res["secure_url"]
            else:
                filename = secure_filename(file.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                image_url = filepath
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            image=image_url,
        )
        db.session.add(product)
        db.session.commit()
        flash("Producto agregado")
        return redirect(url_for("admin.manage_store"))
    return render_template("admin/add_edit_product.html")


@admin_bp.route("/reports")
@activated_required
def manage_reports():
    reports = Report.query.all()
    return render_template("admin/manage_reports.html", reports=reports)


@admin_bp.route("/run-ranking")
@activated_required
def run_ranking():
    calculate_weekly_ranking()
    flash("Ranking recalculado")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/verificaciones")
@activated_required
def verifications():
    users = User.query.filter_by(verification_level=0).all()
    return render_template("admin/verifications.html", users=users)


@admin_bp.route("/verificaciones/<int:user_id>/approve", methods=["POST"])
@activated_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.verification_level = 2
    db.session.commit()
    record_auth_event(user, "verify_student")
    flash("Usuario verificado")
    return redirect(url_for("admin.verifications"))
