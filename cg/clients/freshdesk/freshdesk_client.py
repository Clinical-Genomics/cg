import logging

import requests

from cg.clients.freshdesk.constants import EndPoints
from cg.clients.freshdesk.models import Ticket

LOG = logging.getLogger(__name__)


class FreshdeskClient:
    """Client for communicating with the freshdesk REST API."""

    def __init__(self):
        self.api_key = None
        self.url = None

    def init_app(self, url, api_key):
        """Set up the client."""
        self.url = url
        self.api_key = api_key

    def create_ticket(self, ticket: Ticket) -> Ticket:
        """Create a ticket."""
        LOG.debug(ticket.model_dump_json())
        response = requests.post(
            url=f"{self.url}{EndPoints.TICKETS}",
            headers={"Content-Type": "application/json"},
            auth=(self.api_key, "X"),
            json=ticket.model_dump(exclude_none=True),
        )
        return Ticket.model_validate(response.json())
