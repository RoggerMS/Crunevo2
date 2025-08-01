from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    abort,
    current_app,
)
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models import (
    User,
    Note,
    Post,
    Club,
    Mission,
    Purchase,
    Report,
    Credit,
    AdminLog,
    Product,
    ProductLog,
    UserActivity,
    FeedItem,
    SiteConfig,
    VerificationRequest,
    EmailToken,
    Comment,
    PostComment,
    NoteVote,
    PostReaction,
    SavedPost,
    PostImage,
    PageView,
    PrintRequest,
    ProductRequest,
    SystemErrorLog,
)
from crunevo.utils.helpers import admin_required
from crunevo.utils.credits import add_credit
from crunevo.utils.ranking import calculate_weekly_ranking
from crunevo.constants.credit_reasons import CreditReasons
from crunevo.utils.image_optimizer import upload_optimized_image
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import csv
import io
from flask import make_response

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
@login_required
@admin_required
def require_admin():
    """Ensure admin access and log each admin visit."""
    if request.endpoint != "admin.admin_logs":
        log_admin_action(f"Accessed {request.path}")


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

    # Registration stats using first EmailToken per user
    subq = (
        db.session.query(
            EmailToken.user_id, db.func.min(EmailToken.created_at).label("joined")
        )
        .group_by(EmailToken.user_id)
        .subquery()
    )
    registrations = (
        db.session.query(
            db.func.date(subq.c.joined).label("d"), db.func.count().label("c")
        )
        .filter(subq.c.joined >= week_ago.date())
        .group_by(db.func.date(subq.c.joined))
        .all()
    )
    reg_map = {r.d: r.c for r in registrations}
    reg_labels = []
    reg_counts = []
    for i in range(7):
        day = week_ago.date() + timedelta(days=i)
        reg_labels.append(day.strftime("%d/%m"))
        reg_counts.append(reg_map.get(day, 0))

    new_users_week = sum(reg_counts)
    new_notes_week = Note.query.filter(Note.created_at >= week_ago).count()
    new_posts_week = Post.query.filter(Post.created_at >= week_ago).count()

    # Content distribution counts
    content_counts = {
        "Posts": Post.query.count(),
        "Apuntes": Note.query.count(),
        "Comentarios": Comment.query.count() + PostComment.query.count(),
        "Compras": Purchase.query.count(),
    }

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
    unresolved_errors = SystemErrorLog.query.filter_by(resuelto=False).count()

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
        unresolved_errors=unresolved_errors,
        reg_labels=reg_labels,
        reg_counts=reg_counts,
        content_counts=content_counts,
    )


@admin_bp.route("/users", methods=["GET", "POST"])
def manage_users():
    """Enhanced user management with club and mission info"""
    if request.method == "POST":
        abort(403)
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


@admin_bp.route("/users/<int:user_id>/history")
def user_activity(user_id):
    """Display recent activity for a user."""
    user = User.query.get_or_404(user_id)
    activities = (
        UserActivity.query.filter_by(user_id=user.id)
        .order_by(UserActivity.timestamp.desc())
        .all()
    )
    return render_template("admin/user_history.html", user=user, activities=activities)


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
def update_user_role(user_id):
    """Change a user's role."""
    user = User.query.get_or_404(user_id)
    role = request.form.get("role")
    if role not in {"student", "moderator", "admin"}:
        flash("Rol inválido", "danger")
    else:
        user.role = role
        db.session.commit()
        flash("Rol actualizado", "success")
        log_admin_action(f"Cambió rol de {user.username} a {role}")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>/toggle", methods=["GET"])
def toggle_user_status(user_id):
    """Activate or deactivate a user."""
    user = User.query.get_or_404(user_id)
    user.activated = not user.activated
    db.session.commit()
    flash(
        "Usuario activado" if user.activated else "Usuario desactivado",
        "success",
    )
    log_admin_action(
        f"Toggled user {user.username} to {'activo' if user.activated else 'inactivo'}"
    )
    return redirect(url_for("admin.manage_users"))


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


@admin_bp.route("/creditos")
def manage_creditos_alias():
    """Alias spanish route that forwards to manage_credits."""
    return redirect(url_for("admin.manage_credits"))


@admin_bp.route("/credits")
def manage_credits():
    """View and filter credit history."""
    user_id = request.args.get("user_id", type=int)
    reason = request.args.get("reason")

    query = db.session.query(Credit, User).join(User, Credit.user_id == User.id)
    if user_id:
        query = query.filter(Credit.user_id == user_id)
    if reason:
        query = query.filter(Credit.reason == reason)

    credits = query.order_by(Credit.timestamp.desc()).all()
    return render_template("admin/manage_credits.html", credits=credits)


@admin_bp.route("/credits/export")
def export_credits():
    """Export credit history to CSV."""
    output = io.StringIO()
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

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=credits_export.csv"
    return response


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


@admin_bp.route("/export/products")
def export_products():
    """Export products to CSV"""
    products = Product.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nombre", "Precio", "Crolars", "Stock"])
    for p in products:
        writer.writerow(
            [
                p.id,
                p.name,
                f"{p.price:.2f}",
                p.price_credits or "",
                p.stock,
            ]
        )

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=products_export.csv"
    return response


@admin_bp.route("/store/history")
def product_history():
    """View history of product actions"""
    logs = (
        db.session.query(ProductLog, Product)
        .join(Product, ProductLog.product_id == Product.id)
        .order_by(ProductLog.timestamp.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/product_history.html", logs=logs)


@admin_bp.route("/store")
def manage_store():
    """Admin interface for managing store products."""
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin/manage_store.html", products=products)


@admin_bp.route("/notes")
def manage_notes():
    """Admin interface for managing uploaded notes."""
    notes = (
        db.session.query(Note, User)
        .join(User, Note.user_id == User.id)
        .order_by(Note.created_at.desc())
        .all()
    )
    return render_template("admin/manage_notes.html", notes=notes)


@admin_bp.route("/export/notes")
def export_notes():
    """Export notes to CSV"""
    notes = db.session.query(Note, User).join(User, Note.user_id == User.id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Título", "Autor", "Vistas", "Descargas", "Likes", "Fecha"])
    for note, user in notes:
        writer.writerow(
            [
                note.id,
                note.title,
                user.username,
                note.views,
                note.downloads,
                note.likes,
                (
                    note.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if note.created_at
                    else ""
                ),
            ]
        )
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=notes_export.csv"
    return response


@admin_bp.route("/verificaciones")
def verification_requests():
    """List pending verification requests."""
    requests = VerificationRequest.query.filter_by(status="pending").all()
    return render_template("admin/verification_requests.html", requests=requests)


@admin_bp.route("/verificaciones/<int:request_id>/approve", methods=["POST"])
def approve_verification(request_id):
    """Approve a verification request."""
    req = VerificationRequest.query.get_or_404(request_id)
    user = req.user
    user.verification_level = 2
    req.status = "approved"
    db.session.commit()
    flash("Usuario verificado", "success")
    log_admin_action(f"Aprob\u00f3 verificacion {user.id}")
    return redirect(url_for("admin.verification_requests"))


@admin_bp.route("/pending-comments")
def pending_comments():
    """Review queue for anonymous comments."""
    post_comments = (
        db.session.query(PostComment, Post, User)
        .join(Post, PostComment.post_id == Post.id)
        .outerjoin(User, PostComment.author_id == User.id)
        .filter(PostComment.pending.is_(True))
        .all()
    )
    note_comments = (
        db.session.query(Comment, Note, User)
        .join(Note, Comment.note_id == Note.id)
        .outerjoin(User, Comment.user_id == User.id)
        .filter(Comment.pending.is_(True))
        .all()
    )
    return render_template(
        "admin/pending_comments.html",
        post_comments=post_comments,
        note_comments=note_comments,
    )


@admin_bp.route("/pending-comments/<string:ctype>/<int:cid>/approve", methods=["POST"])
def approve_comment(ctype, cid):
    """Approve a pending comment."""
    model = PostComment if ctype == "post" else Comment
    comment = model.query.get_or_404(cid)
    comment.pending = False
    if isinstance(comment, Comment):
        comment.note.comments_count += 1
    db.session.commit()
    flash("Comentario aprobado", "success")
    log_admin_action(f"Aprob\u00f3 comentario {cid}")
    return redirect(url_for("admin.pending_comments"))


@admin_bp.route("/pending-comments/<string:ctype>/<int:cid>/reject", methods=["POST"])
def reject_comment(ctype, cid):
    """Delete a pending comment."""
    model = PostComment if ctype == "post" else Comment
    comment = model.query.get_or_404(cid)
    db.session.delete(comment)
    db.session.commit()
    flash("Comentario eliminado", "success")
    log_admin_action(f"Elimin\u00f3 comentario {cid}")
    return redirect(url_for("admin.pending_comments"))


@admin_bp.route("/products/new", methods=["POST"])
def add_product():
    """Legacy add product route blocked for moderators."""
    flash("Acción no permitida", "danger")
    return redirect(url_for("admin.manage_store"))


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    """Edit an existing product."""
    product = Product.query.get_or_404(product_id)
    if request.method == "POST":
        product.name = request.form.get("name", product.name)
        product.description = request.form.get("description")
        product.price = request.form.get("price", type=float) or 0
        product.price_credits = request.form.get("price_credits", type=int)
        product.stock = request.form.get("stock", type=int) or 0
        product.is_featured = bool(request.form.get("is_featured"))
        product.credits_only = bool(request.form.get("credits_only"))
        product.is_popular = bool(request.form.get("is_popular"))
        product.is_new = bool(request.form.get("is_new"))
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file and image_file.filename:
                url = upload_optimized_image(image_file, folder="products")
                if url:
                    product.image = url
        db.session.commit()
        log_admin_action(f"Editó producto {product.id}")
        flash("Producto actualizado", "success")
        return redirect(url_for("admin.manage_store"))
    return render_template("admin/add_edit_product.html", product=product)


@admin_bp.route("/prints")
def manage_prints():
    """List and manage queued print requests."""
    prints = (
        db.session.query(PrintRequest, User, Note)
        .join(User, PrintRequest.user_id == User.id)
        .join(Note, PrintRequest.note_id == Note.id)
        .order_by(PrintRequest.requested_at.desc())
        .all()
    )
    return render_template("admin/manage_prints.html", prints=prints)


@admin_bp.route("/product-requests")
def product_requests():
    reqs = (
        db.session.query(ProductRequest, User)
        .join(User, ProductRequest.user_id == User.id)
        .order_by(ProductRequest.created_at.desc())
        .all()
    )
    return render_template("admin/product_requests.html", requests=reqs)


@admin_bp.route("/product-requests/<int:req_id>/update", methods=["POST"])
def update_product_request(req_id):
    pr = ProductRequest.query.get_or_404(req_id)
    status = request.form.get("status")
    if status not in {"approved", "rejected", "pending"}:
        flash("Estado inválido", "danger")
        return redirect(url_for("admin.product_requests"))
    pr.status = status
    pr.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Solicitud actualizada", "success")
    log_admin_action(f"Actualizó solicitud {req_id} a {status}")
    return redirect(url_for("admin.product_requests"))


@admin_bp.route("/prints/<int:print_id>/fulfill", methods=["POST"])
def fulfill_print(print_id):
    """Mark a print request as fulfilled."""
    pr = PrintRequest.query.get_or_404(print_id)
    pr.fulfilled = True
    pr.fulfilled_at = datetime.utcnow()
    db.session.commit()
    flash("Impresión completada", "success")
    log_admin_action(f"Marcó impresión {print_id} como completada")
    return redirect(url_for("admin.manage_prints"))


@admin_bp.route("/logs")
def admin_logs():
    """View recent admin actions"""
    logs = (
        db.session.query(AdminLog, User)
        .join(User, AdminLog.admin_id == User.id)
        .order_by(AdminLog.timestamp.desc())
        .limit(200)
        .all()
    )
    return render_template("admin/admin_logs.html", logs=logs)


@admin_bp.route("/errores")
def ver_errores():
    """List recent system errors for admins"""
    ruta = request.args.get("ruta", "")
    user = request.args.get("user", type=int)
    estado = request.args.get("estado")
    query = SystemErrorLog.query
    if ruta:
        query = query.filter(SystemErrorLog.ruta.contains(ruta))
    if user:
        query = query.filter_by(user_id=user)
    if estado == "resuelto":
        query = query.filter_by(resuelto=True)
    elif estado == "pendiente":
        query = query.filter_by(resuelto=False)
    errores = query.order_by(SystemErrorLog.timestamp.desc()).limit(100).all()
    return render_template(
        "admin/errores.html",
        errores=errores,
        filtro_ruta=ruta,
        filtro_user=user,
        filtro_estado=estado,
    )


@admin_bp.route("/errores/<int:error_id>/resolver", methods=["POST"])
def resolver_error(error_id):
    """Mark a system error as resolved."""
    err = SystemErrorLog.query.get_or_404(error_id)
    err.resuelto = True
    db.session.commit()
    flash("Error marcado como resuelto", "success")
    return redirect(url_for("admin.ver_errores"))


@admin_bp.route("/run-ranking")
def run_ranking():
    """Manually recalculate the weekly ranking."""
    calculate_weekly_ranking()
    log_admin_action("Recalcul\u00f3 ranking semanal")
    flash("Ranking recalculado", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/toggle-maintenance", methods=["POST"])
def toggle_maintenance():
    """Toggle maintenance mode."""
    current = current_app.config.get("MAINTENANCE_MODE", False)
    new_value = not current
    current_app.config["MAINTENANCE_MODE"] = new_value

    cfg = SiteConfig.query.filter_by(key="maintenance_mode").first()
    if cfg:
        cfg.value = "1" if new_value else "0"
    else:
        cfg = SiteConfig(key="maintenance_mode", value="1" if new_value else "0")
        db.session.add(cfg)
    db.session.commit()

    log_admin_action(
        "Activ\u00f3 mantenimiento" if new_value else "Desactiv\u00f3 mantenimiento"
    )
    flash(
        (
            "Modo mantenimiento activado"
            if new_value
            else "Modo mantenimiento desactivado"
        ),
        "success",
    )
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/set-post-retention", methods=["POST"])
def set_post_retention():
    """Update inactive post retention period in days."""
    days = request.form.get("days", type=int)
    if not days or days < 1:
        flash("Número de días inválido", "danger")
        return redirect(url_for("admin.dashboard"))

    current_app.config["POST_RETENTION_DAYS"] = days
    cfg = SiteConfig.query.filter_by(key="post_retention_days").first()
    if cfg:
        cfg.value = str(days)
    else:
        cfg = SiteConfig(key="post_retention_days", value=str(days))
        db.session.add(cfg)
    db.session.commit()

    log_admin_action(f"Actualizó retención de posts a {days} días")
    flash("Retención de posts actualizada", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route(
    "/delete-post/<int:post_id>", methods=["POST"], endpoint="delete_post_admin"
)
def delete_post_admin(post_id):
    """Allow admins to delete any post."""
    post = Post.query.get_or_404(post_id)
    FeedItem.query.filter_by(item_type="post", ref_id=post.id).delete()
    PostReaction.query.filter_by(post_id=post.id).delete()
    PostComment.query.filter_by(post_id=post.id).delete()
    PostImage.query.filter_by(post_id=post.id).delete()
    SavedPost.query.filter_by(post_id=post.id).delete()
    db.session.delete(post)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            "No se pudo eliminar la publicaci\u00f3n por registros relacionados",
            "danger",
        )
        return redirect(url_for("admin.manage_reports"))
    log_admin_action(f"Elimin\u00f3 post {post_id}")
    flash("Post eliminado", "success")
    return redirect(url_for("admin.manage_reports"))


@admin_bp.route(
    "/delete-note/<int:note_id>", methods=["POST"], endpoint="delete_note_admin"
)
def delete_note_admin(note_id):
    """Allow admins to delete any note."""
    note = Note.query.get_or_404(note_id)
    FeedItem.query.filter_by(item_type="apunte", ref_id=note.id).delete()
    Credit.query.filter_by(
        user_id=note.user_id, related_id=note.id, reason=CreditReasons.APUNTE_SUBIDO
    ).delete()
    NoteVote.query.filter_by(note_id=note.id).delete()
    Comment.query.filter_by(note_id=note.id).delete()
    PrintRequest.query.filter_by(note_id=note.id).delete()
    db.session.delete(note)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("No se pudo eliminar el apunte por registros relacionados", "danger")
        return redirect(url_for("admin.manage_reports"))
    log_admin_action(f"Elimin\u00f3 apunte {note_id}")
    flash("Apunte eliminado", "success")
    return redirect(url_for("admin.manage_reports"))


@admin_bp.route(
    "/products/<int:product_id>/delete", methods=["POST"], endpoint="delete_product"
)
def delete_product(product_id):
    """Delete a product from the store."""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    log_admin_action(f"Elimin\u00f3 producto {product_id}")
    flash("Producto eliminado", "success")
    return redirect(url_for("admin.product_history"))


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


@admin_bp.route("/pageviews")
def pageviews():
    """Display heatmap of page views."""
    week_ago = datetime.utcnow() - timedelta(days=6)
    rows = (
        db.session.query(
            PageView.path,
            db.func.date(PageView.timestamp).label("d"),
            db.func.count().label("c"),
        )
        .filter(PageView.timestamp >= week_ago)
        .group_by(PageView.path, db.func.date(PageView.timestamp))
        .all()
    )
    totals = {}
    for r in rows:
        totals[r.path] = totals.get(r.path, 0) + r.c
    top_paths = [
        p for p, _ in sorted(totals.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    days = [week_ago.date() + timedelta(days=i) for i in range(7)]
    matrix = []
    for y, path in enumerate(top_paths):
        for x, day in enumerate(days):
            count = 0
            for r in rows:
                if r.path == path and r.d == day:
                    count = r.c
                    break
            matrix.append({"x": x, "y": y, "v": count})
    labels_x = [d.strftime("%d/%m") for d in days]
    labels_y = top_paths
    return render_template(
        "admin/pageviews.html",
        matrix_data=matrix,
        labels_x=labels_x,
        labels_y=labels_y,
    )


@admin_bp.route("/api/analytics")
def analytics_api():
    """Return analytics data with optional filters."""
    days_param = request.args.get("days", "30d")
    try:
        if days_param.endswith("d"):
            num_days = int(days_param[:-1])
        elif days_param.endswith("y"):
            num_days = int(days_param[:-1]) * 365
        else:
            num_days = int(days_param)
    except ValueError:
        num_days = 30

    since = datetime.utcnow() - timedelta(days=num_days)

    active_users = (
        db.session.query(UserActivity.user_id)
        .filter(UserActivity.timestamp >= since)
        .distinct()
        .count()
    )

    new_notes = Note.query.filter(Note.created_at >= since).count()
    new_posts = Post.query.filter(Post.created_at >= since).count()

    likes = PostReaction.query.filter(PostReaction.timestamp >= since).count()
    comments = (
        Comment.query.filter(Comment.created_at >= since).count()
        + PostComment.query.filter(PostComment.timestamp >= since).count()
    )

    purchases_q = Purchase.query.filter(Purchase.timestamp >= since)
    total_purchases = purchases_q.count()
    total_revenue = (
        db.session.query(db.func.coalesce(db.func.sum(Purchase.price_soles), 0))
        .filter(Purchase.timestamp >= since)
        .scalar()
    )
    avg_order_value = float(total_revenue) / total_purchases if total_purchases else 0

    data = {
        "users": {"active_users": active_users, "growth_rate": 0},
        "content": {
            "new_notes": new_notes,
            "new_posts": new_posts,
            "total_likes": likes,
            "total_comments": comments,
        },
        "commerce": {
            "total_revenue": float(total_revenue),
            "total_purchases": total_purchases,
            "avg_order_value": avg_order_value,
            "conversion_rate": 0,
        },
    }

    return jsonify(data)


def log_admin_action(action):
    """Log admin actions"""
    log = AdminLog(admin_id=current_user.id, action=action, timestamp=datetime.utcnow())
    db.session.add(log)
    db.session.commit()
