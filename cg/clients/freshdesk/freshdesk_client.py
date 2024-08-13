import logging
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory

from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cg.clients.freshdesk.constants import EndPoints
from cg.clients.freshdesk.utils import handle_client_errors
from cg.clients.freshdesk.models import TicketCreate, TicketResponse
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile, WriteStream

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
        """Create a ticket."""
        ticket_data = ticket.model_dump(exclude_none=True)

        if attachments:
            files = [
                ("attachments[]", (attachment.name, open(attachment, "rb")))
                for attachment in attachments
            ]
            response: Response = self.session.post(
                url=self._url(EndPoints.TICKETS), data=ticket_data, files=files
            )
        else:
            response: Response = self.session.post(
                url=self._url(EndPoints.TICKETS), json=ticket_data
            )

        response.raise_for_status()
        return TicketResponse.model_validate(response.json())

    def _url(self, endpoint: str) -> str:
        """Get the full URL for the endpoint."""
        return f"{self.base_url}{endpoint}"

    @handle_client_errors
    def _get_session(self) -> Session:
        session = Session()
        session.auth = (self.api_key, "X")
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
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

    @staticmethod
    def create_new_ticket_attachment(content: dict, file_name: str) -> dict:
        return {
            file_name: TEXT_FILE_ATTACH_PARAMS.format(
                content=WriteStream.write_stream_from_content(
                    content=content, file_format=FileFormat.JSON
                )
            )
        }

    @staticmethod
    def create_connecting_ticket_attachment(content: dict) -> TemporaryDirectory:
        directory = TemporaryDirectory()
        WriteFile.write_file_from_content(
            content=content,
            file_format=FileFormat.JSON,
            file_path=Path(directory.name, "order.json"),
        )
        return directory
