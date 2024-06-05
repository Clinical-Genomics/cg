import logging

import requests

from cg.clients.freshdesk.constants import EndPoints
from cg.clients.freshdesk.models import TicketCreate, TicketResponse

LOG = logging.getLogger(__name__)


class FreshdeskClient:
    """Client for communicating with the freshdesk REST API."""

    def __init__(self):
        self.headers = None
        self.api_key = None
        self.url = None

    def init_app(self, url: str, api_key: str):
        """Set up the client."""
        self.url = url
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}

    @property
    def auth_header(self):
        return self.api_key, "X"

    def create_ticket(self, ticket: TicketCreate) -> TicketResponse:
        """Create a ticket."""
        LOG.debug(ticket.model_dump_json())
        response = requests.post(
            url=f"{self.url}{EndPoints.TICKETS}",
            headers=self.headers,
            auth=self.auth_header,
            json=ticket.model_dump(exclude_none=True),
        )
        return TicketResponse.model_validate(response.json())
