import logging
from http import HTTPStatus
from pathlib import Path

from requests import HTTPError, Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cg.clients.freshdesk.constants import EndPoints
from cg.clients.freshdesk.models import TicketCreate, TicketResponse
from cg.clients.freshdesk.utils import handle_client_errors, prepare_attachments
from cg.exc import (
    FreshdeskDeliveryMessageError,
    FreshdeskGetTicketError,
    FreshdeskUpdateTicketError,
)

LOG = logging.getLogger(__name__)


class FreshdeskClient:
    """Client for communicating with the freshdesk REST API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = self._get_session()

    @handle_client_errors
    def create_ticket(self, ticket: TicketCreate, attachments: list[Path] = None) -> TicketResponse:
        """Create a ticket with multipart form data."""
        multipart_data = ticket.to_multipart_data()
        files = prepare_attachments(attachments) if attachments else None

        response = self.session.post(
            url=f"{self.base_url}{EndPoints.TICKETS}", data=multipart_data, files=files
        )
        response.raise_for_status()
        return TicketResponse.model_validate(response.json())

    @handle_client_errors
    def _get_session(self) -> Session:
        session = Session()
        session.auth = (self.api_key, "X")
        self._configure_retries(session)
        return session

    @staticmethod
    def _configure_retries(session: Session) -> None:
        """Configures retries for the session."""
        retry_strategy = Retry(
            total=5,
            status_forcelist=[
                HTTPStatus.TOO_MANY_REQUESTS,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                HTTPStatus.BAD_GATEWAY,
                HTTPStatus.SERVICE_UNAVAILABLE,
                HTTPStatus.GATEWAY_TIMEOUT,
            ],
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

    def get_ticket(self, ticket_id: int) -> TicketResponse:
        url = f"{self.base_url}{EndPoints.TICKETS}/{ticket_id}"
        LOG.debug(f"URL={url}")
        try:
            response = self.session.get(url=url)
            response.raise_for_status()
            return TicketResponse.model_validate(response.json()["ticket"])
        except HTTPError as error:
            raise FreshdeskGetTicketError from error

    def update_ticket(self, ticket_id: int, status: int) -> TicketResponse:
        url = f"{self.base_url}{EndPoints.TICKETS}/{ticket_id}"
        data = {"status": status}
        LOG.debug(f"URL={url}; JSON={data}")
        try:
            response = self.session.put(url=url, data=data)
            response.raise_for_status()
            return TicketResponse.model_validate(response.json()["ticket"])
        except HTTPError as error:
            raise FreshdeskUpdateTicketError from error

    def reply_to_ticket(self, ticket_id: int, message: str) -> None:
        """Send a reply to an existing ticket in Freshdesk."""
        url = f"{self.base_url}{EndPoints.TICKETS}/{ticket_id}/reply"
        data = {"body": message}
        LOG.debug(f"URL={url}; JSON={data}")
        try:
            response = self.session.post(url=url, data=data)
            response.raise_for_status()
        except HTTPError as error:
            raise FreshdeskDeliveryMessageError from error
