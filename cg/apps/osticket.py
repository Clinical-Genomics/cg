import json
import logging
import os.path

import requests
from flask import Flask

from cg.exc import TicketCreationError

LOG = logging.getLogger(__name__)
TEXT_FILE_ATTACH_PARAMS = "data:text/plain;charset=utf-8,{content}"


class OsTicket(object):

    """Interface to ticket system."""

    def __init__(self):
        self.headers = None
        self.url = None

    def init_app(self, app: Flask):
        """Initialize the API in Flask."""
        self.setup(api_key=app.config["OSTICKET_API_KEY"], domain=app.config["OSTICKET_DOMAIN"])

    def setup(self, api_key: str = None, domain: str = None):
        """Initialize the API."""
        self.headers = {"X-API-Key": api_key}
        self.url = os.path.join(domain, "api/tickets.json")

    def open_ticket(
        self, attachment: dict, email: str, message: str, name: str, subject: str
    ) -> int:
        """Open a new ticket through the REST API."""
        data = dict(
            name=name,
            email=email,
            subject=subject,
            message=message,
            attachments=[attachment],
        )
        res = requests.post(self.url, json=data, headers=self.headers)
        if res.ok:
            return int(res.text)
        LOG.error("res.text: %s, reason: %s", res.text, res.reason)
        raise TicketCreationError(res)

    @staticmethod
    def create_attachment(content: dict, file_name: str) -> dict:
        return {file_name: TEXT_FILE_ATTACH_PARAMS.format(content=json.dumps(content))}
