"""Mock the os ticket api"""

import logging
import os.path
from typing import Optional

from cg.apps.osticket import OsTicket
from cg.exc import TicketCreationError
from flask import Flask

LOG = logging.getLogger(__name__)


class MockOsTicket(OsTicket):

    """Interface to ticket system."""

    def __init__(self):
        self.headers = None
        self.url = None
        self._ticket_nr: int = 123456
        self._should_fail: bool = False
        self._return_none: bool = False

    def set_ticket_nr(self, number: int) -> None:
        self._ticket_nr = number

    def init_app(self, app: Flask):
        """Initialize the API in Flask."""

    def setup(self, api_key: str = None, domain: str = None):
        """Initialize the API."""
        self.headers = {"X-API-Key": api_key}
        self.url = os.path.join(domain, "api/tickets.json")

    def open_ticket(self, name: str, email: str, subject: str, message: str) -> Optional[int]:
        """Open a new ticket through the REST API."""
        if self._should_fail:
            LOG.error("res.text: %s, reason: %s", self._ticket_nr, "Unknown reason")
            raise TicketCreationError("FAIL")
        if self._return_none:
            return None

        return self._ticket_nr
