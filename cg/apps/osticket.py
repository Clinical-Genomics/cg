from pathlib import Path

import logging
import os.path
from tempfile import TemporaryDirectory

import requests
from flask import Flask

from cg.constants.constants import FileFormat
from cg.exc import TicketCreationError
from cg.io.controller import WriteStream, WriteFile

LOG = logging.getLogger(__name__)
TEXT_FILE_ATTACH_PARAMS = "data:text/plain;charset=utf-8,{content}"


class OsTicket(object):

    """Interface to ticket system"""

    def __init__(self):
        self.headers = None
        self.url = None
        self.osticket_email = None
        self.email_uri = None

    def init_app(self, app: Flask):
        """Initialize the API in Flask"""
        self.setup(
            api_key=app.config["OSTICKET_API_KEY"],
            domain=app.config["OSTICKET_DOMAIN"],
            osticket_email=app.config["SUPPORT_SYSTEM_EMAIL"],
            email_uri=app.config["EMAIL_URI"],
        )

    def setup(
        self,
        api_key: str = None,
        domain: str = None,
        osticket_email: str = None,
        email_uri: str = None,
    ):
        """Initialize the API"""
        self.headers = {"X-API-Key": api_key}
        self.url = os.path.join(domain, "api/tickets.json")
        self.osticket_email = osticket_email
        self.email_uri = email_uri

    def open_ticket(
        self, attachment: dict, email: str, message: str, name: str, subject: str
    ) -> str:
        """Open a new ticket through the REST API"""
        data = dict(
            name=name,
            email=email,
            subject=subject,
            message=message,
            attachments=[attachment],
        )
        res = requests.post(self.url, json=data, headers=self.headers)
        if res.ok:
            return res.text
        LOG.error("res.text: %s, reason: %s", res.text, res.reason)
        raise TicketCreationError(res)

    @staticmethod
    def create_new_ticket_attachment(content: dict, file_name: str) -> dict:
        return {
            file_name: TEXT_FILE_ATTACH_PARAMS.format(
                content=WriteStream.write_stream_from_content(
                    content=content, file_format=FileFormat.JSON
                )
            )
        }

    @staticmethod
    def create_connecting_ticket_attachment(content: dict) -> TemporaryDirectory:
        directory = TemporaryDirectory()
        WriteFile.write_file_from_content(
            content=content,
            file_format=FileFormat.JSON,
            file_path=Path(directory.name, "order.json"),
        )
        return directory
