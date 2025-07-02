from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from markupsafe import escape

from crunevo.utils.mailer import send_email
from crunevo.utils.helpers import admin_required
from crunevo.utils.audit import record_auth_event

admin_email_bp = Blueprint("admin_email", __name__, url_prefix="/admin")


@admin_email_bp.route("/send-email", methods=["GET", "POST"])
@login_required
@admin_required
def send_admin_email():
    if request.method == "POST":
        recipient = escape(request.form.get("to", "").strip())
        subject = escape(request.form.get("subject", "").strip())
        html_content = request.form.get("content", "")

        if not recipient or not subject or not html_content:
            flash("Todos los campos son obligatorios", "danger")
            return render_template("admin/send_email.html")

        success, error = send_email(recipient, subject, html_content)
        if success:
            flash("Correo enviado correctamente", "success")
            record_auth_event(current_user, "admin_send_email")
        else:
            flash("No se pudo enviar el correo", "danger")
            if error:
                flash(error, "danger")

        return redirect(url_for("admin_email.send_admin_email"))

    return render_template("admin/send_email.html")
