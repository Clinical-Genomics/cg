"""Mock the os ticket api"""

import logging
import os.path

from flask import Flask

from cg.apps.osticket import OsTicket
from cg.exc import TicketCreationError

LOG = logging.getLogger(__name__)


class MockOsTicket(OsTicket):
    """Interface to ticket system."""

    def __init__(self):
        self.headers = None
        self.url = None
        self.osticket_email = "james.holden@scilifelab.se"
        self.mail_container_uri = "dummy_uri"
        self._ticket_nr: str = "123456"
        self._should_fail: bool = False
        self._return_none: bool = False
        self.email_uri = "http://localhost:0000/sendmail"

    def set_ticket_nr(self, ticket_id: str) -> None:
        self._ticket_nr = ticket_id

    def init_app(self, app: Flask):
        """Initialize the API in Flask."""

    def setup(
        self,
        api_key: str = None,
        domain: str = None,
        osticket_email: str = None,
        email_uri: str = None,
    ):
        """Initialize the API."""
        self.headers = {"X-API-Key": api_key}
        self.url = os.path.join(domain, "api/tickets.json")

    def open_ticket(
        self, attachment: dict, email: str, message: str, name: str, subject: str
    ) -> str | None:
        """Open a new ticket through the REST API."""
        if self._should_fail:
            LOG.error("res.text: %s, reason: %s", self._ticket_nr, "Unknown reason")
            raise TicketCreationError("FAIL")
        if self._return_none:
            return None

        return self._ticket_nr
