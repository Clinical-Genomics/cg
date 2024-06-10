import logging

import requests
from pydantic import ValidationError
from requests import RequestException
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cg.clients.freshdesk.constants import TO_MANY_REQUESTS_CODE, EndPoints
from cg.clients.freshdesk.exceptions import (
    FreshdeskAPIException,
    FreshdeskModelException,
)
from cg.clients.freshdesk.models import TicketCreate, TicketResponse

LOG = logging.getLogger(__name__)


class FreshdeskClient:
    """Client for communicating with the freshdesk REST API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = self._configure_session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def create_ticket(self, ticket: TicketCreate) -> TicketResponse:
        """Create a ticket."""
        LOG.debug(ticket.model_dump_json())
        try:
            response = self.session.post(
                url=f"{self.base_url}{EndPoints.TICKETS}",
                json=ticket.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            ticket_response: TicketResponse = TicketResponse.model_validate(response.json())
        except RequestException as error:
            LOG.error(f"Could not create ticket: {error}")
            raise FreshdeskAPIException(error) from error
        except ValidationError as error:
            LOG.error(f"Response from Freshdesk does not fit model: {TicketResponse}.\n{error}")
            raise FreshdeskModelException(error) from error
        return ticket_response

    def _configure_session(self):
        session = requests.Session()
        self._configure_retries(session)
        session.auth = (self.api_key, "X")
        session.headers.update({"Content-Type": "application/json"})
        return session

    @staticmethod
    def _configure_retries(session: requests.Session) -> None:
        retry_strategy = Retry(
            total=5,
            status_forcelist=[TO_MANY_REQUESTS_CODE],
            allowed_methods=None,
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
