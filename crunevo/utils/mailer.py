from flask_mail import Message
from flask import current_app, flash
from crunevo.extensions import mail


def send_email(to, subject, html):
    msg = Message(subject=subject, recipients=[to], html=html)
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error("Email error: %s", e)
        flash(
            "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
            "danger",
        )
