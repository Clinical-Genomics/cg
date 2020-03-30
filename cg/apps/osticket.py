import logging
import os.path

from flask import Flask
import requests

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

    def open_ticket(self, name: str, email: str, subject: str, message: str) -> str:
        """Open a new ticket through the REST API."""
        data = dict(name=name, email=email, subject=subject, message=message)
        res = requests.post(self.url, json=data, headers=self.headers)
        if res.ok:
            return res.text
        else:
            LOG.error("res.text: %s, reason: %s", res.text, res.reason)
            raise TicketCreationError(res)
