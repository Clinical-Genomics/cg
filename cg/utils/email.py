from smtplib import SMTP

from cg.exc import EmailNotSentError
from cg.models.email import EmailInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_mail(email_info: EmailInfo):
    """Email handler. Sending new user request email to admin"""

    print(email_info.json())
    with SMTP(email_info.smtp_server) as server:
        msg = MIMEMultipart()
        msg["From"] = email_info.sender_email
        msg["To"] = email_info.receiver_email
        msg["Subject"] = email_info.subject
        msg.attach(MIMEText(email_info.message, "plain"))
        server.sendmail(email_info.sender_email, email_info.receiver_email, msg.as_string())
    # except:
    #   raise EmailNotSentError(message=f"Email could not be sent")
