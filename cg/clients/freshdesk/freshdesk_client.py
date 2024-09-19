from http import HTTPStatus
from pathlib import Path

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cg.clients.freshdesk.constants import EndPoints
from cg.clients.freshdesk.models import ReplyCreate, TicketCreate, TicketResponse
from cg.clients.freshdesk.utils import handle_client_errors, prepare_attachments


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

    @handle_client_errors
    def reply_to_ticket(self, reply: ReplyCreate, attachments: list[Path] = None) -> None:
        """Send a reply to an existing ticket in Freshdesk."""
        url = f"{self.base_url}{EndPoints.TICKETS}/{reply.ticket_number}/reply"

        files = prepare_attachments(attachments) if attachments else None
        multipart_data = reply.to_multipart_data()

        response = self.session.post(url=url, data=multipart_data, files=files)
        response.raise_for_status()
