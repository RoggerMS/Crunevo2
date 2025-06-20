import os
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    Response,
    abort,
)
from flask_login import login_required, current_user
from crunevo.utils.helpers import (
    activated_required,
    admin_required,
    full_admin_required,
)
import csv
from io import StringIO
from werkzeug.utils import secure_filename
from crunevo.extensions import db
from crunevo.models import (
    User,
    Product,
    Report,
    Note,
    Credit,
    Comment,
    ProductLog,
    AdminNotification,
)
from crunevo.utils.ranking import calculate_weekly_ranking
from crunevo.utils.audit import record_auth_event
from crunevo.utils.stats import (
    user_registrations_last_7_days,
    notes_last_4_weeks,
    credits_last_4_weeks,
    products_last_3_months,
)
import cloudinary.uploader

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def restrict_to_subdomain():
    if current_app.config.get("TESTING"):
        return
    host = request.host.split(":")[0]
    if not host.startswith("burrito."):
        abort(403)


@admin_bp.before_request
@login_required
@admin_required
def before_admin():
    unread = AdminNotification.query.filter_by(
        admin_id=current_user.id, read=False
    ).all()
    for note in unread:
        flash(note.message)
        note.read = True
    if unread:
        db.session.commit()


@admin_bp.route("/")
@admin_required
def dashboard():
    users_total = User.query.count()
    notes_total = Note.query.count()
    comments_total = Comment.query.count()
    products_total = Product.query.count()
    credits_total = db.session.query(db.func.sum(Credit.amount)).scalar() or 0
    last_ranking = (
        db.session.query(Credit)
        .filter(Credit.reason == "ranking")
        .order_by(Credit.id.desc())
        .first()
    )
    stats = {
        "users": user_registrations_last_7_days(),
        "notes": notes_last_4_weeks(),
        "credits": credits_last_4_weeks(),
        "products": products_last_3_months(),
    }
    return render_template(
        "admin/dashboard.html",
        users_total=users_total,
        notes_total=notes_total,
        comments_total=comments_total,
        products_total=products_total,
        credits_total=credits_total,
        last_ranking=last_ranking,
        stats=stats,
    )


@admin_bp.route("/users", methods=["GET", "POST"])
@activated_required
def manage_users():
    if request.method == "POST":
        if current_user.role != "admin":
            abort(403)
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
@full_admin_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description")
        price = float(request.form["price"])
        stock = int(request.form.get("stock", 0))
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
        log = ProductLog(
            product_id=product.id, action="created", admin_id=current_user.id
        )
        db.session.add(log)
        notif = AdminNotification(
            admin_id=current_user.id,
            title="Producto agregado",
            message=f"Se agregó {product.name}",
        )
        db.session.add(notif)
        db.session.commit()
        flash("Producto agregado")
        return redirect(url_for("admin.manage_store"))
    return render_template("admin/add_edit_product.html")


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@full_admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form["name"]
        product.description = request.form.get("description")
        product.price = float(request.form["price"])
        product.stock = int(request.form["stock"])
        file = request.files.get("image")
        if file and file.filename:
            cloud_url = current_app.config.get("CLOUDINARY_URL")
            if cloud_url:
                res = cloudinary.uploader.upload(file)
                product.image = res["secure_url"]
            else:
                filename = secure_filename(file.filename)
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                product.image = filepath
        db.session.commit()
        log = ProductLog(
            product_id=product.id, action="edited", admin_id=current_user.id
        )
        db.session.add(log)
        notif = AdminNotification(
            admin_id=current_user.id,
            title="Producto actualizado",
            message=f"Se actualizó {product.name}",
        )
        db.session.add(notif)
        db.session.commit()
        flash("Producto actualizado correctamente")
        return redirect(url_for("admin.manage_store"))
    return render_template("admin/add_edit_product.html", product=product)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@full_admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    log = ProductLog(product_id=product.id, action="deleted", admin_id=current_user.id)
    db.session.add(log)
    db.session.commit()
    flash("Producto eliminado correctamente")
    return redirect(url_for("admin.manage_store"))


@admin_bp.route("/reports")
@activated_required
def manage_reports():
    reports = Report.query.all()
    return render_template("admin/manage_reports.html", reports=reports)


@admin_bp.route("/run-ranking")
@activated_required
@full_admin_required
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


@admin_bp.route("/user/<int:user_id>/role", methods=["POST"])
@full_admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    if new_role in ["student", "admin"]:
        user.role = new_role
        db.session.commit()
        flash("Rol actualizado correctamente")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/user/<int:user_id>/toggle_status")
@full_admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.activated = not user.activated
    db.session.commit()
    flash("Estado de cuenta actualizado")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/user/<int:user_id>/activity")
@admin_required
def user_activity(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("admin/user_activity.html", user=user)


@admin_bp.route("/credits")
@admin_required
def manage_credits():
    credits = (
        db.session.query(Credit, User)
        .join(User, Credit.user_id == User.id)
        .order_by(Credit.timestamp.desc())
        .all()
    )
    return render_template("admin/manage_credits.html", credits=credits)


@admin_bp.route("/users/export")
@admin_required
def export_users():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Email", "Rol", "Créditos", "Estado"])
    for user in User.query.all():
        writer.writerow(
            [
                user.id,
                user.username,
                user.email,
                user.role,
                user.credits,
                "Activo" if user.activated else "Inactivo",
            ]
        )
    headers = {"Content-Disposition": "attachment; filename=users.csv"}
    return Response(output.getvalue(), mimetype="text/csv", headers=headers)


@admin_bp.route("/credits/export")
@admin_required
def export_credits():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Usuario", "Email", "Monto", "Razón", "Fecha"])
    credits = (
        db.session.query(Credit, User)
        .join(User, Credit.user_id == User.id)
        .order_by(Credit.timestamp.desc())
        .all()
    )
    for credit, user in credits:
        writer.writerow(
            [
                credit.id,
                user.username,
                user.email,
                credit.amount,
                credit.reason,
                credit.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )
    headers = {"Content-Disposition": "attachment; filename=credits.csv"}
    return Response(output.getvalue(), mimetype="text/csv", headers=headers)


@admin_bp.route("/store/export")
@admin_required
def export_products():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Precio", "Stock", "URL de imagen"])
    for product in Product.query.all():
        writer.writerow(
            [
                product.id,
                product.name,
                product.price,
                product.stock,
                product.image,
            ]
        )
    headers = {"Content-Disposition": "attachment; filename=products.csv"}
    return Response(output.getvalue(), mimetype="text/csv", headers=headers)


@admin_bp.route("/store/history")
@activated_required
def product_history():
    logs = (
        db.session.query(ProductLog, Product)
        .join(Product, ProductLog.product_id == Product.id)
        .order_by(ProductLog.timestamp.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/product_history.html", logs=logs)
