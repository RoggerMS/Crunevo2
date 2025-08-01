from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user
import cloudinary.uploader
from crunevo.extensions import db
from crunevo.models.club import Club, ClubMember
from crunevo.utils.credits import add_credit
from crunevo.constants.credit_reasons import CreditReasons
from crunevo.forms import ClubForm
from datetime import datetime

club_bp = Blueprint("club", __name__)


@club_bp.route("/clubes")
def list_clubs():
    clubs = Club.query.all()
    user_clubs = []
    if current_user.is_authenticated:
        user_clubs = [
            cm.club_id
            for cm in ClubMember.query.filter_by(user_id=current_user.id).all()
        ]

    return render_template("club/list.html", clubs=clubs, user_clubs=user_clubs)


@club_bp.route("/club/<int:club_id>")
def view_club(club_id):
    club = Club.query.get_or_404(club_id)
    is_member = False
    is_creator = False
    user_role = None

    if current_user.is_authenticated:
        membership = ClubMember.query.filter_by(
            user_id=current_user.id, club_id=club_id
        ).first()
        is_member = membership is not None
        is_creator = club.is_creator(current_user)
        user_role = membership.role if membership else None

    # Get club posts
    from crunevo.models.club_post import ClubPost

    posts = (
        ClubPost.query.filter_by(club_id=club_id)
        .order_by(ClubPost.created_at.desc())
        .limit(20)
        .all()
    )

    members = ClubMember.query.filter_by(club_id=club_id).limit(10).all()
    return render_template(
        "club/detail.html",
        club=club,
        is_member=is_member,
        is_creator=is_creator,
        user_role=user_role,
        members=members,
        posts=posts,
    )


@club_bp.route("/club/<int:club_id>/post", methods=["POST"])
@login_required
def create_club_post(club_id):

    # Check if user is a member
    membership = ClubMember.query.filter_by(
        user_id=current_user.id, club_id=club_id
    ).first()
    if not membership:
        flash("Debes ser miembro del club para publicar", "error")
        return redirect(url_for("club.view_club", club_id=club_id))

    content = request.form.get("content")
    if not content or len(content.strip()) < 5:
        flash("El contenido debe tener al menos 5 caracteres", "error")
        return redirect(url_for("club.view_club", club_id=club_id))

    from crunevo.models.club_post import ClubPost

    post = ClubPost(club_id=club_id, author_id=current_user.id, content=content.strip())

    db.session.add(post)
    db.session.commit()

    # Award credits
    add_credit(current_user, 1, CreditReasons.ACTIVIDAD_SOCIAL, related_id=post.id)

    flash("¡Publicación creada en el club!")
    return redirect(url_for("club.view_club", club_id=club_id))


@club_bp.route("/club/<int:club_id>/join", methods=["POST"])
@login_required
def join_club(club_id):
    club = Club.query.get_or_404(club_id)

    # Check if already a member
    existing = ClubMember.query.filter_by(
        user_id=current_user.id, club_id=club_id
    ).first()
    if existing:
        return jsonify({"error": "Ya eres miembro de este club"}), 400

    # Join club
    membership = ClubMember(user_id=current_user.id, club_id=club_id)
    db.session.add(membership)

    # Update member count
    club.member_count += 1
    db.session.commit()

    # Award credits
    add_credit(current_user, 2, CreditReasons.ACTIVIDAD_SOCIAL, related_id=club_id)

    flash(f"¡Te has unido al club {club.name}!")
    return jsonify({"success": True, "member_count": club.member_count})


@club_bp.route("/club/<int:club_id>/leave", methods=["POST"])
@login_required
def leave_club(club_id):
    club = Club.query.get_or_404(club_id)
    membership = ClubMember.query.filter_by(
        user_id=current_user.id, club_id=club_id
    ).first()

    if not membership:
        return jsonify({"error": "No eres miembro de este club"}), 400

    # Prevent creator from leaving if they're the only admin
    if club.is_creator(current_user):
        other_admins = (
            ClubMember.query.filter_by(club_id=club_id, role="admin")
            .filter(ClubMember.user_id != current_user.id)
            .count()
        )
        if other_admins == 0:
            return (
                jsonify(
                    {
                        "error": "No puedes dejar el club siendo el único administrador. Transfiere el rol primero."
                    }
                ),
                400,
            )

    db.session.delete(membership)
    club.member_count -= 1
    db.session.commit()

    flash(f"Has dejado el club {club.name}")
    return jsonify({"success": True, "member_count": club.member_count})


def upload_to_cloudinary(file, folder="clubs"):
    """Upload file to Cloudinary and return URL"""
    try:
        cloud_url = current_app.config.get("CLOUDINARY_URL")
        if not cloud_url:
            return None

        result = cloudinary.uploader.upload(
            file,
            resource_type="auto",
            folder=folder,
            quality="auto:good",
            fetch_format="auto",
        )
        return result.get("secure_url")
    except Exception as e:
        current_app.logger.error(f"Error uploading to Cloudinary: {e}")
        return None


@club_bp.route("/clubes/crear", methods=["GET", "POST"])
@login_required
def create_club():
    """Create a new club"""
    form = ClubForm()
    if form.validate_on_submit():
        # Upload files to Cloudinary
        avatar_url = None
        banner_url = None

        if form.avatar.data:
            avatar_url = upload_to_cloudinary(form.avatar.data, "clubs/avatars")

        if form.banner.data:
            banner_url = upload_to_cloudinary(form.banner.data, "clubs/banners")

        club = Club(
            name=form.name.data.strip(),
            career=form.career.data.strip(),
            description=(
                form.description.data.strip() if form.description.data else None
            ),
            avatar_url=avatar_url,
            banner_url=banner_url,
            facebook_url=(
                form.facebook_url.data.strip() if form.facebook_url.data else None
            ),
            whatsapp_url=(
                form.whatsapp_url.data.strip() if form.whatsapp_url.data else None
            ),
            creator_id=current_user.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(club)
        db.session.flush()

        # Create admin membership for creator
        membership = ClubMember(user_id=current_user.id, club_id=club.id, role="admin")
        club.member_count = 1
        db.session.add(membership)
        db.session.commit()

        # Award credits for creating a club
        add_credit(current_user, 5, CreditReasons.ACTIVIDAD_SOCIAL, related_id=club.id)

        flash("Club creado exitosamente", "success")
        return redirect(url_for("club.view_club", club_id=club.id))

    return render_template("club/create_club.html", form=form)


@club_bp.route("/club/<int:club_id>/editar", methods=["GET", "POST"])
@login_required
def edit_club(club_id):
    """Edit an existing club - only creator and admins allowed"""
    club = Club.query.get_or_404(club_id)

    # Check permissions: only creator or admin role users
    if not club.is_creator(current_user):
        membership = ClubMember.query.filter_by(
            user_id=current_user.id, club_id=club_id
        ).first()
        if not membership or membership.role not in ["admin"]:
            flash("No tienes permisos para editar este club", "error")
            return redirect(url_for("club.view_club", club_id=club_id))

    form = ClubForm(edit_mode=True)

    if form.validate_on_submit():
        # Upload new files if provided
        if form.avatar.data:
            new_avatar = upload_to_cloudinary(form.avatar.data, "clubs/avatars")
            if new_avatar:
                club.avatar_url = new_avatar

        if form.banner.data:
            new_banner = upload_to_cloudinary(form.banner.data, "clubs/banners")
            if new_banner:
                club.banner_url = new_banner

        # Update club data
        club.name = form.name.data.strip()
        club.career = form.career.data.strip()
        club.description = (
            form.description.data.strip() if form.description.data else None
        )
        club.facebook_url = (
            form.facebook_url.data.strip() if form.facebook_url.data else None
        )
        club.whatsapp_url = (
            form.whatsapp_url.data.strip() if form.whatsapp_url.data else None
        )

        db.session.commit()
        flash("Club actualizado exitosamente", "success")
        return redirect(url_for("club.view_club", club_id=club.id))

    # Pre-populate form with current data
    elif request.method == "GET":
        form.name.data = club.name
        form.career.data = club.career
        form.description.data = club.description
        form.facebook_url.data = club.facebook_url
        form.whatsapp_url.data = club.whatsapp_url

    return render_template("club/edit_club.html", form=form, club=club)
