from flask import (
    Blueprint,
    render_template,
    send_file,
    flash,
    redirect,
    url_for,
    session,
)
from flask_login import login_required, current_user
from crunevo.extensions import db, oauth
from crunevo.models.certificate import Certificate
from crunevo.utils.certificate_generator import (
    generate_certificate_pdf,
    check_certificate_eligibility,
)
from crunevo.utils.linkedin import build_share_url, post_to_linkedin

cert_bp = Blueprint("certificate", __name__)
certificate_bp = cert_bp


@cert_bp.route("/certificados")
@login_required
def list_certificates():
    """List user's certificates and available ones"""
    user_certificates = Certificate.query.filter_by(user_id=current_user.id).all()
    eligible = check_certificate_eligibility(current_user)

    # Group certificates by type
    issued = {cert.certificate_type: cert for cert in user_certificates}

    certificate_info = {
        "participacion": {
            "title": "Certificado de Participación",
            "description": "Por ser miembro activo de CRUNEVO",
            "requirements": "Estar registrado en la plataforma",
        },
        "misiones": {
            "title": "Certificado de Logros Académicos",
            "description": "Por completar 10 misiones",
            "requirements": "10 misiones completadas",
        },
        "apuntes": {
            "title": "Certificado de Contribución",
            "description": "Por subir 3 o más apuntes",
            "requirements": "3 apuntes subidos",
        },
    }

    return render_template(
        "certificates/list.html",
        issued=issued,
        eligible=eligible,
        certificate_info=certificate_info,
    )


@cert_bp.route("/certificados/generar/<certificate_type>")
@login_required
def generate_certificate(certificate_type):
    """Generate and issue a certificate"""
    eligible = check_certificate_eligibility(current_user)

    if certificate_type not in eligible:
        flash("No cumples los requisitos para este certificado", "error")
        return redirect(url_for("certificate.list_certificates"))

    # Check if already issued
    existing = Certificate.query.filter_by(
        user_id=current_user.id, certificate_type=certificate_type
    ).first()

    if not existing:
        # Create certificate record
        cert_titles = {
            "participacion": "Certificado de Participación en CRUNEVO",
            "misiones": "Certificado de Logros Académicos",
            "apuntes": "Certificado de Contribución Educativa",
        }

        certificate = Certificate(
            user_id=current_user.id,
            certificate_type=certificate_type,
            title=cert_titles.get(certificate_type, "Certificado CRUNEVO"),
        )
        db.session.add(certificate)
        db.session.commit()

    # Generate PDF
    pdf_buffer = generate_certificate_pdf(current_user, certificate_type)
    if not pdf_buffer:
        flash("Error al generar el certificado", "error")
        return redirect(url_for("certificate.list_certificates"))

    filename = f"certificado_{certificate_type}_{current_user.username}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


@cert_bp.route("/certificados/descargar/<int:cert_id>")
@login_required
def download_certificate(cert_id):
    """Download an existing certificate"""
    certificate = Certificate.query.filter_by(
        id=cert_id, user_id=current_user.id
    ).first_or_404()

    pdf_buffer = generate_certificate_pdf(current_user, certificate.certificate_type)
    if not pdf_buffer:
        flash("Error al generar el certificado", "error")
        return redirect(url_for("certificate.list_certificates"))

    filename = f"certificado_{certificate.certificate_type}_{current_user.username}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


@cert_bp.route("/certificados/linkedin/authorize")
@login_required
def linkedin_authorize():
    redirect_uri = url_for("certificate.linkedin_callback", _external=True)
    return oauth.linkedin.authorize_redirect(redirect_uri)


@cert_bp.route("/certificados/linkedin/callback")
@login_required
def linkedin_callback():
    token = oauth.linkedin.authorize_access_token()
    profile = oauth.linkedin.get("me?projection=(id)").json()
    session["linkedin_token"] = token
    session["linkedin_id"] = profile.get("id")
    next_url = session.pop("linkedin_next", url_for("certificate.list_certificates"))
    flash("LinkedIn conectado", "success")
    return redirect(next_url)


@cert_bp.route("/certificados/linkedin/share/<int:cert_id>")
@login_required
def share_certificate_link(cert_id):
    Certificate.query.filter_by(id=cert_id, user_id=current_user.id).first_or_404()
    cert_url = url_for(
        "certificate.download_certificate", cert_id=cert_id, _external=True
    )
    return redirect(build_share_url(cert_url))


@cert_bp.route("/certificados/linkedin/post/<int:cert_id>")
@login_required
def post_certificate_linkedin(cert_id):
    certificate = Certificate.query.filter_by(
        id=cert_id, user_id=current_user.id
    ).first_or_404()
    if "linkedin_token" not in session or "linkedin_id" not in session:
        session["linkedin_next"] = url_for(
            "certificate.post_certificate_linkedin", cert_id=cert_id
        )
        return redirect(url_for("certificate.linkedin_authorize"))
    cert_url = url_for(
        "certificate.download_certificate", cert_id=cert_id, _external=True
    )
    text = f"He obtenido el {certificate.title} en CRUNEVO!"
    success = post_to_linkedin(
        session["linkedin_id"],
        session["linkedin_token"]["access_token"],
        text,
        cert_url,
    )
    flash(
        "Publicado en LinkedIn" if success else "No se pudo publicar en LinkedIn",
        "success" if success else "error",
    )
    return redirect(url_for("certificate.list_certificates"))
