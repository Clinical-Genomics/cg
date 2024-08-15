import logging
from http import HTTPStatus
from pathlib import Path

from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from typing import Dict, Union

from cg.clients.freshdesk.constants import EndPoints
from cg.clients.freshdesk.models import TicketCreate, TicketResponse
from cg.clients.freshdesk.utils import handle_client_errors, prepare_attachments

LOG = logging.getLogger(__name__)
TEXT_FILE_ATTACH_PARAMS = "data:text/plain;charset=utf-8,{content}"


class FreshdeskClient:
    """Client for communicating with the freshdesk REST API."""

    def __init__(self, base_url: str, api_key: str, order_email_id: int, env: str):
        self.base_url = base_url
        self.api_key = api_key
        self.order_email_id = order_email_id
        self.env = env
        self.session = self._get_session()

    @handle_client_errors
    def create_ticket(self, ticket: TicketCreate, attachments: list[Path] = None) -> TicketResponse:
        """Create a ticket with multipart form data."""
        ticket_data = self._convert_ticket_to_multipart_data(ticket)
        files = prepare_attachments(attachments) if attachments else None

        LOG.info(ticket_data)
        response: Response = self.session.post(
            url=f"{self.base_url}{EndPoints.TICKETS}", data=ticket_data, files=files
        )
        response.raise_for_status()
        return TicketResponse.model_validate(response.json())

    def _convert_ticket_to_multipart_data(self, ticket: TicketCreate) -> Dict[str, Union[str, int]]:
        """Convert the TicketCreate model into a flat dictionary for multipart form data."""
        data = []

        for field, value in ticket.model_dump(exclude_none=True).items():
            if isinstance(value, list) and field == "tags":
                for i, tag in enumerate(value):
                    data.append(("tags[]", tag))
            elif isinstance(value, dict) and field == "custom_fields":
                for key, val in value.items():
                    data.append((f"custom_fields[{key}]", val))
            else:
                data.append((field, value))

        return data

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
