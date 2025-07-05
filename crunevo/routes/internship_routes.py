from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.internship import Internship, InternshipApplication

internship_bp = Blueprint("internship", __name__)


@internship_bp.route("/internships")
def list_internships():
    field = request.args.get("field", "")
    location = request.args.get("location", "")
    query = Internship.query
    if field:
        query = query.filter(Internship.field.ilike(f"%{field}%"))
    if location:
        query = query.filter(Internship.location.ilike(f"%{location}%"))
    internships = query.order_by(Internship.posted_at.desc()).all()
    return render_template(
        "internship/list.html",
        internships=internships,
        field=field,
        location=location,
    )


@internship_bp.route("/internships/<int:internship_id>")
def view_internship(internship_id):
    internship = Internship.query.get_or_404(internship_id)
    has_applied = False
    if current_user.is_authenticated:
        has_applied = (
            InternshipApplication.query.filter_by(
                internship_id=internship.id, user_id=current_user.id
            ).first()
            is not None
        )
    return render_template(
        "internship/detail.html", internship=internship, has_applied=has_applied
    )


@internship_bp.route("/internships/post", methods=["GET", "POST"])
@login_required
def post_internship():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        field = request.form.get("field")
        location = request.form.get("location")
        company = request.form.get("company")
        internship = Internship(
            title=title,
            description=description,
            field=field,
            location=location,
            company=company,
        )
        db.session.add(internship)
        db.session.commit()
        flash("Práctica publicada correctamente")
        return redirect(url_for("internship.list_internships"))
    return render_template("internship/post.html")


@internship_bp.route("/internships/<int:internship_id>/apply", methods=["POST"])
@login_required
def apply_internship(internship_id):
    Internship.query.get_or_404(internship_id)
    cover_letter = request.form.get("cover_letter")
    existing = InternshipApplication.query.filter_by(
        internship_id=internship_id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({"error": "Ya aplicaste"}), 400
    application = InternshipApplication(
        internship_id=internship_id,
        user_id=current_user.id,
        cover_letter=cover_letter,
    )
    db.session.add(application)
    db.session.commit()
    flash("Aplicación enviada")
    return jsonify({"success": True})
