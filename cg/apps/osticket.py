import json
import logging
import os.path
from typing import Optional, List

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
        self, name: str, email: str, attachments: List[dict], subject: str, message: str
    ) -> Optional[int]:
        """Open a new ticket through the REST API."""
        data = dict(
            name=name,
            email=email,
            subject=subject,
            message=message,
            attachments=attachments,
        )
        res = requests.post(self.url, json=data, headers=self.headers)
        if res.ok:
            try:
                return int(res.text)
            except ValueError:
                LOG.error("Could not convert res %s to int", res.text)
                return None

        LOG.error("res.text: %s, reason: %s", res.text, res.reason)
        raise TicketCreationError(res)

    @staticmethod
    def create_attachments(
        order_dict: dict,
        file_name: str = "order.json",
    ) -> List[dict]:
        return [{file_name: TEXT_FILE_ATTACH_PARAMS.format(content=json.dumps(order_dict))}]
