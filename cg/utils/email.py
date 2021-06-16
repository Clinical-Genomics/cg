from smtplib import SMTP

from email.message import EmailMessage
from cg.exc import EmailNotSentError
from cg.models.email import EmailInfo


def send_mail(email_info: EmailInfo):
    """Email handler. Sending new user request email to admin"""

    try:
        with SMTP(email_info.smtp_server) as server:
            msg = EmailMessage()
            msg.set_content(email_info.message)
            msg["Subject"] = email_info.subject
            msg["From"] = email_info.sender_email
            msg["To"] = email_info.receiver_email
            server.send_message(msg)
    except:
        raise EmailNotSentError(message=f"Email could not be sent")
