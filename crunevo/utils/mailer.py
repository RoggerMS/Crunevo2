import os
import requests
from flask_mail import Message
from flask import current_app, flash
from crunevo.extensions import mail


RESEND_API_KEY = os.getenv("RESEND_API_KEY")


def send_email(to, subject, html):
    if RESEND_API_KEY:
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": current_app.config.get("MAIL_DEFAULT_SENDER"),
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=5,
            )
            current_app.logger.info("Resend response: %s", resp.text)
            resp.raise_for_status()
            return
        except Exception as e:
            current_app.logger.error("Email error: %s", e)
            flash(
                "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
                "danger",
            )
            return

    msg = Message(subject=subject, recipients=[to], html=html)
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error("Email error: %s", e)
        flash(
            "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
            "danger",
        )
