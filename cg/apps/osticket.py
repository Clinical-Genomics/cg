import logging
import os.path
from typing import Optional

import requests
from flask import Flask

from cg.exc import TicketCreationError

LOG = logging.getLogger(__name__)


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

    def open_ticket(self, name: str, email: str, subject: str, message: str) -> Optional[int]:
        """Open a new ticket through the REST API."""
        data = dict(name=name, email=email, subject=subject, message=message)
        res = requests.post(self.url, json=data, headers=self.headers)
        if res.ok:
            try:
                return int(res.text)
            except ValueError:
                LOG.error("Could not convert res %s to int", res.text)
                return None
        else:
            LOG.error("res.text: %s, reason: %s", res.text, res.reason)
            raise TicketCreationError(res)
