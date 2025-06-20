import requests
from flask_mail import Message
from flask import current_app, flash
from crunevo.extensions import mail


def send_email(to, subject, html):
    key = current_app.config.get("RESEND_API_KEY")
    provider = current_app.config.get("MAIL_PROVIDER")
    if provider == "resend" and key:
        sender = current_app.config.get("MAIL_USERNAME", "noreply@crunevo.com")
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "from": f"CRUNEVO <{sender}>",
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=5,
            )
            current_app.logger.info("Resend response: %s", resp.text)
            if resp.status_code != 200:
                flash(
                    "No se pudo enviar el correo de confirmación. Inténtalo más tarde.",
                    "danger",
                )
                current_app.logger.warning(
                    "Resend failed with status %s", resp.status_code
                )
            return resp.status_code == 200
        except Exception as e:
            current_app.logger.error("Email error: %s", e)
            flash(
                "No se pudo enviar el correo de confirmaci\u00f3n. Int\u00e9ntalo m\u00e1s tarde.",
                "danger",
            )
            return False

    msg = Message(subject=subject, recipients=[to], html=html)
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error("Email error: %s", e)
        flash(
            "No se pudo enviar el correo de confirmaci\u00f3n. Int\u00e9ntalo m\u00e1s tarde.",
            "danger",
        )
        return False
