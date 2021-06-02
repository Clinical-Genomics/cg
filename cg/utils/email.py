import smtplib
import ssl
from email.message import EmailMessage
from cg.exc import EmailNotSentError
from cg.models.email import EmailInfo


def send_mail(email_info: EmailInfo):
    """Email handler. Sending new user request email to admin"""

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            email_info.smtp_server, email_info.sll_port, context=context
        ) as server:
            server.login(email_info.sender_email, email_info.sender_password)
            msg = EmailMessage()
            msg.set_content(email_info.message)
            msg["Subject"] = email_info.subject
            msg["From"] = email_info.sender_email
            msg["To"] = email_info.receiver_email
            server.send_message(msg)
    except:
        raise EmailNotSentError(message=f"Email could not be sent")
