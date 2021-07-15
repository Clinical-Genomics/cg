from smtplib import SMTP

from cg.exc import EmailNotSentError
from cg.models.email import EmailInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def send_mail(email_info: EmailInfo) -> None:
    """Email handler. Sending new user request email to admin"""

    with SMTP(email_info.smtp_server) as server:
        msg = MIMEMultipart("mixed")
        msg["From"] = email_info.sender_email
        msg["To"] = email_info.receiver_email
        msg["Subject"] = email_info.subject
        msg.attach(MIMEText(email_info.message, "plain"))
        if email_info.file:
            file_attachment = MIMEApplication(open(email_info.file, "rb").read())
            file_attachment.add_header(
                "Content-Disposition", "attachment", filename=email_info.file.name
            )
            msg.attach(file_attachment)
        try:
            server.connect()
            server.sendmail(
                from_addr=email_info.sender_email,
                to_addrs=email_info.receiver_email.split(","),
                msg=msg.as_string(),
            )
        except Exception:
            raise EmailNotSentError(message=f"Email could not be sent")
