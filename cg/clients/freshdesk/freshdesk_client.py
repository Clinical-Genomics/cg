import logging

import requests

from cg.clients.freshdesk.models import Reply, ReplyResponse, Ticket, TicketResponse

LOG = logging.getLogger(__name__)


class FreshdeskClient:
    """Freshdesk client."""

    def __init__(self):
        self.api_key = None
        self.url = None

    def set_up_client(self, url, api_key):
        """Set up client."""
        self.url = url
        self.api_key = api_key

    def create_ticket(self, ticket: Ticket) -> TicketResponse:
        """Create ticket."""
        url = self.url + "/api/v2/tickets"
        headers = {"Content-Type": "application/json"}
        LOG.debug(ticket.model_dump_json())
        response = requests.post(
            url,
            headers=headers,
            auth=(self.api_key, "X"),
            json=ticket.model_dump(exclude_none=True),
        )
        return TicketResponse.model_validate(response.json())

    def post_reply(self, ticket_id, reply: Reply):
        """Post reply to ticket."""
        url = f"{self.url}/api/v2/tickets/{ticket_id}/reply"
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url, headers=headers, auth=(self.api_key, "X"), json=reply.model_dump(exclude_none=True)
        )
        return ReplyResponse.model_validate(response.json())

    def update_ticket(self, ticket: Ticket):
        """Close ticket."""
        url = self.url + f"/api/v2/tickets/{ticket.id}"
        headers = {"Content-Type": "application/json"}
        return requests.put(
            url,
            headers=headers,
            auth=(self.api_key, "X"),
            json=ticket.model_dump(exclude_none=True),
        )
