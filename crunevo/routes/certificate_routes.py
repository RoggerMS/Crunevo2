from flask import Blueprint, render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from crunevo.extensions import db
from crunevo.models.certificate import Certificate
from crunevo.utils.certificate_generator import (
    generate_certificate_pdf,
    check_certificate_eligibility,
)

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
