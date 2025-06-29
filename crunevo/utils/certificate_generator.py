import io
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors


def generate_certificate_pdf(user, certificate_type):
    """Generate a certificate PDF for the user"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)

    # Certificate data
    certificates_data = {
        "participacion": {
            "title": "Certificado de Participación",
            "description": f"Se certifica que {user.username} ha sido un miembro activo de la comunidad educativa CRUNEVO",
            "achievement": "Participación Activa en la Plataforma",
        },
        "misiones": {
            "title": "Certificado de Logros Académicos",
            "description": f"Se certifica que {user.username} ha completado exitosamente 10 misiones académicas",
            "achievement": "Completar 10 Misiones",
        },
        "apuntes": {
            "title": "Certificado de Contribución Educativa",
            "description": f"Se certifica que {user.username} ha contribuido con 3 o más apuntes de calidad",
            "achievement": "Contribuidor de Contenido Educativo",
        },
    }

    cert_data = certificates_data.get(certificate_type)
    if not cert_data:
        return None

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor("#6f42c1"),
        alignment=1,  # Center
    )

    subtitle_style = ParagraphStyle(
        "CertSubtitle",
        parent=styles["Normal"],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor("#495057"),
        alignment=1,
    )

    body_style = ParagraphStyle(
        "CertBody",
        parent=styles["Normal"],
        fontSize=14,
        spaceAfter=15,
        alignment=1,
        leading=20,
    )

    # Content
    content = []

    # Header
    content.append(Paragraph("CRUNEVO", title_style))
    content.append(Paragraph("Red Educativa Universitaria", subtitle_style))
    content.append(Spacer(1, 20))

    # Certificate title
    content.append(Paragraph(cert_data["title"], title_style))
    content.append(Spacer(1, 30))

    # Description
    content.append(Paragraph(cert_data["description"], body_style))
    content.append(Spacer(1, 20))

    # Achievement
    content.append(Paragraph(f"<b>Logro:</b> {cert_data['achievement']}", body_style))
    content.append(Spacer(1, 30))

    # Date and signature area
    date_str = datetime.now().strftime("%d de %B de %Y")
    content.append(Paragraph(f"Emitido el {date_str}", body_style))
    content.append(Spacer(1, 40))

    # Generate QR code for profile
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    profile_url = (
        f"https://crunevo.com/perfil/{user.username}"  # Adjust domain as needed
    )
    qr.add_data(profile_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Footer with QR and signature

    content.append(Paragraph("___________________", body_style))
    content.append(Paragraph("Equipo CRUNEVO", body_style))
    content.append(Spacer(1, 20))
    content.append(
        Paragraph(
            f"QR: Perfil de {user.username}",
            ParagraphStyle("QR", parent=styles["Normal"], fontSize=10, alignment=1),
        )
    )

    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer


def check_certificate_eligibility(user):
    """Check which certificates the user is eligible for"""
    eligible = []

    # Always eligible for participation
    eligible.append("participacion")

    # Check missions completed (assuming we have a way to count them)
    completed_missions = len(user.missions) if hasattr(user, "missions") else 0
    if completed_missions >= 10:
        eligible.append("misiones")

    # Check notes uploaded
    notes_count = len(user.notes) if user.notes else 0
    if notes_count >= 3:
        eligible.append("apuntes")

    return eligible
