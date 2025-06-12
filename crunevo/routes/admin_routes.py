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
from crunevo.utils.helpers import activated_required
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from crunevo.models import User, Product, Report
from crunevo.utils.ranking import calculate_weekly_ranking
from crunevo.utils.helpers import admin_required
from crunevo.utils.audit import record_auth_event
import cloudinary.uploader

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@activated_required
@admin_required
def dashboard():
    user_count = User.query.count()
    return render_template("admin/dashboard.html", user_count=user_count)


@admin_bp.route("/users")
@activated_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template("admin/manage_users.html", users=users)


@admin_bp.route("/store", methods=["GET", "POST"])
@activated_required
@admin_required
def manage_store():
    products = Product.query.all()
    return render_template("admin/manage_store.html", products=products)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@activated_required
@admin_required
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
@admin_required
def manage_reports():
    reports = Report.query.all()
    return render_template("admin/manage_reports.html", reports=reports)


@admin_bp.route("/run-ranking")
@activated_required
@admin_required
def run_ranking():
    calculate_weekly_ranking()
    flash("Ranking recalculado")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/verificaciones")
@activated_required
@admin_required
def verifications():
    users = User.query.filter_by(verification_level=0).all()
    return render_template("admin/verifications.html", users=users)


@admin_bp.route("/verificaciones/<int:user_id>/approve", methods=["POST"])
@activated_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.verification_level = 2
    db.session.commit()
    record_auth_event(user, "verify_student")
    flash("Usuario verificado")
    return redirect(url_for("admin.verifications"))
