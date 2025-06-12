from flask_mail import Message
from crunevo.extensions import mail


def send_email(to, subject, html):
    msg = Message(subject=subject, recipients=[to], html=html)
    mail.send(msg)
