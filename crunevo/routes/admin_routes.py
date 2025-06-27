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
    Post,
    FeedItem,
    Credit,
    Achievement,
    Mission,
    UserMission,
    Comment,
    PostComment,
    ProductLog,
    AdminNotification,
    AdminLog,
    RankingCache,
)
from crunevo.utils.ranking import calculate_weekly_ranking
from crunevo.utils import unlock_achievement
from crunevo.utils import send_notification
from crunevo.utils.audit import record_auth_event
from crunevo.utils.stats import (
    user_registrations_last_7_days,
    notes_last_4_weeks,
    credits_last_4_weeks,
    products_last_3_months,
)
from crunevo.constants import CreditReasons
from crunevo.cache.feed_cache import remove_item
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
    # Sort products by tags ensuring None values don't cause errors
    products.sort(
        key=lambda p: (
            bool(p.is_featured),
            bool(p.is_popular),
            bool(p.is_new),
        ),
        reverse=True,
    )
    return render_template("admin/manage_store.html", products=products)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@activated_required
@full_admin_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description")
        price = float(request.form["price"])
        price_credits = request.form.get("price_credits", type=int)
        stock = int(request.form.get("stock", 0))
        is_featured = bool(request.form.get("is_featured"))
        credits_only = bool(request.form.get("credits_only"))
        is_popular = bool(request.form.get("is_popular"))
        is_new = bool(request.form.get("is_new"))
        image_url = None
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file and image_file.filename != "":
                cloud_url = current_app.config.get("CLOUDINARY_URL")
                if cloud_url:
                    res = cloudinary.uploader.upload(image_file)
                    image_url = res["secure_url"]
                else:
                    filename = secure_filename(image_file.filename)
                    upload_folder = current_app.config["UPLOAD_FOLDER"]
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
                    image_url = filepath
        product = Product(
            name=name,
            description=description,
            price=price,
            price_credits=price_credits,
            stock=stock,
            image=image_url,
            is_featured=is_featured,
            credits_only=credits_only,
            is_popular=is_popular,
            is_new=is_new,
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
        product.price_credits = request.form.get("price_credits", type=int)
        product.stock = int(request.form["stock"])
        new_featured = bool(request.form.get("is_featured"))
        product.is_featured = new_featured
        product.credits_only = bool(request.form.get("credits_only"))
        product.is_popular = bool(request.form.get("is_popular"))
        product.is_new = bool(request.form.get("is_new"))
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file and image_file.filename != "":
                cloud_url = current_app.config.get("CLOUDINARY_URL")
                if cloud_url:
                    res = cloudinary.uploader.upload(image_file)
                    product.image = res["secure_url"]
                else:
                    filename = secure_filename(image_file.filename)
                    upload_folder = current_app.config["UPLOAD_FOLDER"]
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    image_file.save(filepath)
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
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("admin/manage_reports.html", reports=reports)


@admin_bp.route("/comentarios")
@activated_required
def manage_comments():
    rep_ids = []
    for r in Report.query.filter_by(status="open").all():
        if r.description.startswith("Comment "):
            try:
                cid = int(r.description.split()[1].split(":")[0])
                rep_ids.append(cid)
            except Exception:
                pass
    post_comments = (
        db.session.query(PostComment, Post, User)
        .join(Post, PostComment.post_id == Post.id)
        .join(User, PostComment.author_id == User.id)
        .filter(PostComment.id.in_(rep_ids))
        .all()
    )
    note_comments = (
        db.session.query(Comment, Note, User)
        .join(Note, Comment.note_id == Note.id)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.id.in_(rep_ids))
        .all()
    )
    return render_template(
        "admin/manage_comments.html",
        post_comments=post_comments,
        note_comments=note_comments,
    )


@admin_bp.route("/comentarios/<int:comment_id>/delete", methods=["POST"])
@activated_required
def delete_comment(comment_id):
    pc = PostComment.query.get(comment_id)
    c = Comment.query.get(comment_id)
    target = pc or c
    if not target:
        abort(404)
    db.session.delete(target)
    db.session.commit()
    db.session.add(
        AdminLog(
            admin_id=current_user.id,
            action="delete_comment",
            target_id=comment_id,
            target_type="post" if pc else "note",
        )
    )
    db.session.commit()
    flash("Comentario eliminado")
    return redirect(url_for("admin.manage_comments"))


@admin_bp.route("/reports/<int:report_id>/resolve", methods=["POST"])
@activated_required
def resolve_report(report_id):
    if current_user.role != "admin":
        abort(403)
    report = Report.query.get_or_404(report_id)
    report.status = "resolved"
    db.session.commit()
    flash("Reporte marcado como resuelto")
    return redirect(url_for("admin.manage_reports"))


@admin_bp.route("/run-ranking")
@activated_required
@full_admin_required
def run_ranking():
    calculate_weekly_ranking()
    flash("Ranking recalculado")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/estadisticas")
@activated_required
def stats_page():
    ranking = (
        db.session.query(RankingCache, User)
        .join(User, RankingCache.user_id == User.id)
        .filter(RankingCache.period == "semanal")
        .order_by(RankingCache.score.desc())
        .limit(10)
        .all()
    )
    stats = {
        "users": user_registrations_last_7_days(),
        "notes": notes_last_4_weeks(),
    }
    return render_template("admin/stats.html", ranking=ranking, stats=stats)


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


@admin_bp.route("/creditos")
@admin_required
def manage_creditos_alias():
    """Alias spanish route that forwards to manage_credits."""
    return redirect(url_for("admin.manage_credits"))


@admin_bp.route("/credits")
@admin_required
def manage_credits():
    user_id = request.args.get("user_id", type=int)
    reason = request.args.get("reason")

    query = db.session.query(Credit, User).join(User, Credit.user_id == User.id)
    if user_id:
        query = query.filter(Credit.user_id == user_id)
    if reason:
        query = query.filter(Credit.reason == reason)

    credits = query.order_by(Credit.timestamp.desc()).all()
    return render_template("admin/manage_credits.html", credits=credits)


@admin_bp.route("/achievements", methods=["GET", "POST"])
@activated_required
def manage_achievements():
    if request.method == "POST":
        code = request.form.get("code")
        title = request.form.get("title")
        description = request.form.get("description")
        icon = request.form.get("icon")
        ach = Achievement(code=code, title=title, description=description, icon=icon)
        db.session.add(ach)
        db.session.commit()
        flash("Logro creado")
        return redirect(url_for("admin.manage_achievements"))
    achievements = Achievement.query.all()
    return render_template("admin/manage_achievements.html", achievements=achievements)


@admin_bp.route("/achievements/assign", methods=["POST"])
@activated_required
def assign_achievement():
    user_id = request.form.get("user_id", type=int)
    ach_id = request.form.get("achievement_id", type=int)
    user = User.query.get_or_404(user_id)
    ach = Achievement.query.get_or_404(ach_id)
    unlock_achievement(user, ach.code)
    flash("Logro asignado")
    return redirect(url_for("admin.manage_achievements"))


@admin_bp.route("/misiones")
@admin_required
def manage_missions():
    """Display claimed missions by users."""
    records = (
        db.session.query(UserMission, User, Mission)
        .join(User, UserMission.user_id == User.id)
        .join(Mission, UserMission.mission_id == Mission.id)
        .order_by(UserMission.completed_at.desc())
        .all()
    )
    return render_template("admin/manage_missions.html", records=records)


@admin_bp.route("/users/export")
@admin_required
def export_users():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Email", "Rol", "Crolars", "Estado"])
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
    writer.writerow(
        [
            "ID",
            "Nombre",
            "Precio S/",
            "Crolars",
            "Stock",
            "URL de imagen",
        ]
    )
    for product in Product.query.all():
        writer.writerow(
            [
                product.id,
                product.name,
                product.price,
                product.price_credits,
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


@admin_bp.route("/logs")
@activated_required
def admin_logs():
    logs = (
        db.session.query(AdminLog, User)
        .join(User, AdminLog.admin_id == User.id)
        .order_by(AdminLog.timestamp.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/admin_logs.html", logs=logs)


@admin_bp.route("/delete-note/<int:note_id>", methods=["POST"])
@activated_required
def delete_note_admin(note_id):
    """Allow an admin to delete a note from the feed."""
    if current_user.role != "admin":
        abort(403)
    note = Note.query.get_or_404(note_id)
    feed_items = FeedItem.query.filter_by(item_type="apunte", ref_id=note.id).all()
    owner_ids = [fi.owner_id for fi in feed_items]
    FeedItem.query.filter_by(item_type="apunte", ref_id=note.id).delete()
    Credit.query.filter_by(
        user_id=note.user_id, related_id=note.id, reason=CreditReasons.APUNTE_SUBIDO
    ).delete()
    db.session.delete(note)
    db.session.commit()
    for uid in owner_ids:
        try:
            remove_item(uid, "apunte", note.id)
        except Exception:
            pass
    send_notification(note.user_id, "Un administrador elimin\u00f3 tu apunte")
    notif = AdminNotification(
        admin_id=current_user.id,
        title="Apunte eliminado",
        message=f"Se elimin\u00f3 el apunte {note_id}",
    )
    db.session.add(notif)
    db.session.add(
        AdminLog(
            admin_id=current_user.id,
            action="delete_note",
            target_id=note_id,
            target_type="note",
        )
    )
    db.session.commit()
    flash("Apunte eliminado")
    return redirect(request.referrer or url_for("feed.view_feed"))


@admin_bp.route("/delete-post/<int:post_id>", methods=["POST"])
@activated_required
def delete_post_admin(post_id):
    """Allow an admin to delete a post from the feed."""
    if current_user.role != "admin":
        abort(403)
    post = Post.query.get_or_404(post_id)
    author_id = post.author_id
    feed_items = FeedItem.query.filter_by(item_type="post", ref_id=post.id).all()
    owner_ids = [fi.owner_id for fi in feed_items]
    FeedItem.query.filter_by(item_type="post", ref_id=post.id).delete()
    db.session.delete(post)
    db.session.commit()
    for uid in owner_ids:
        try:
            remove_item(uid, "post", post.id)
        except Exception:
            pass
    if author_id:
        send_notification(
            author_id, "Un administrador elimin\u00f3 tu publicaci\u00f3n"
        )
    notif = AdminNotification(
        admin_id=current_user.id,
        title="Post eliminado",
        message=f"Se elimin\u00f3 el post {post_id}",
    )
    db.session.add(notif)
    db.session.add(
        AdminLog(
            admin_id=current_user.id,
            action="delete_post",
            target_id=post_id,
            target_type="post",
        )
    )
    db.session.commit()
    flash("Publicaci\u00f3n eliminada")
    return redirect(request.referrer or url_for("feed.view_feed"))
