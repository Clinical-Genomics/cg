import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from sendmail_container import FormDataRequest

from cg.apps.osticket import OsTicket, TEXT_FILE_ATTACH_PARAMS

LOG = logging.getLogger(__name__)


class EmailTicket(OsTicket):
    """Class for placing orders via email"""

    def open_ticket(
        self, attachment: dict, email: str, message: str, name: str, subject: str
    ) -> int:
        """Sends an email with order information to the given email-address"""
        sender_prefix, email_server_alias = email.split("@")
        temp_dir: TemporaryDirectory = self.create_connecting_ticket_attachment(content=attachment)
        email_form = FormDataRequest(
            sender_prefix=sender_prefix,
            email_server_alias=email_server_alias,
            request_uri=self.email_uri,
            recipients=email,
            mail_title=subject,
            mail_body=message[len(TEXT_FILE_ATTACH_PARAMS.format(content="")) :],
            attachments=[Path(f"{temp_dir.name}/order.json")],
        )
        email_form.submit()
        temp_dir.cleanup()
        return 123456

    @staticmethod
    def create_new_ticket_attachment(content: dict, file_name: str) -> dict:
        return content
