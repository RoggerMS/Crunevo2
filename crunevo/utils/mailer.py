import requests
from flask_mail import Message
from flask import current_app
from crunevo.extensions import mail


def send_email(to, subject, html):
    """Send an email using Resend or Flask-Mail.

    Returns
    -------
    tuple
        (success: bool, error_message: Optional[str])
    """

    key = current_app.config.get("RESEND_API_KEY")
    provider = current_app.config.get("MAIL_PROVIDER")
    if isinstance(to, str):
        to_list = [to.strip()]
    else:
        try:
            to_list = [str(addr).strip() for addr in to if addr]
        except TypeError:
            to_list = [str(to).strip()]

    if provider == "resend" and not key:
        current_app.logger.error(
            "MAIL_PROVIDER=resend pero RESEND_API_KEY no est\xc3\xa1 configurada"
        )

    if provider == "resend" and key:
        sender = current_app.config.get("MAIL_USERNAME", "noreply@crunevo.com")
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "from": f"CRUNEVO <{sender}>",
                    "to": to_list,
                    "subject": subject,
                    "html": html,
                },
                timeout=5,
            )
            current_app.logger.info("Resend response: %s", resp.text)
            if resp.status_code == 200:
                return True, None
            err_msg = resp.text
            try:
                data = resp.json()
                err_msg = data.get("error", {}).get("message", err_msg)
            except Exception:
                current_app.logger.exception("Error parsing Resend error response")
            current_app.logger.warning(
                "Resend failed with status %s: %s", resp.status_code, err_msg
            )
            return False, err_msg
        except Exception as e:
            current_app.logger.error("Email error: %s", e)
            return False, str(e)

    msg = Message(subject=subject, recipients=to_list, html=html)
    try:
        mail.send(msg)
        return True, None
    except Exception as e:
        current_app.logger.error("Email error: %s", e)
        return False, str(e)
