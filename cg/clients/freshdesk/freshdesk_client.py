import logging
from http import HTTPStatus

from pydantic import ValidationError
from requests import RequestException, Response, Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cg.clients.freshdesk.constants import EndPoints
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
        self.session = self._get_session()

    def create_ticket(self, ticket: TicketCreate) -> TicketResponse:
        """Create a ticket."""
        LOG.debug(ticket.model_dump_json())
        try:
            response: Response = self.session.post(
                url=self._url(EndPoints.TICKETS),
                json=ticket.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            return TicketResponse.model_validate(response.json())
        except RequestException as error:
            LOG.error(f"Could not create ticket: {error}")
            raise FreshdeskAPIException(error) from error
        except ValidationError as error:
            LOG.error(f"Response from Freshdesk does not fit model: {TicketResponse}.\n{error}")
            raise FreshdeskModelException(error) from error

    def _url(self, endpoint: str) -> str:
        """Get the full URL for the endpoint."""
        return f"{self.base_url}{endpoint}"

    def _get_session(self) -> Session:
        """Configures and sets a session to be used for requests."""
        session = Session()
        self._configure_retries(session)
        session.auth = (self.api_key, "X")
        session.headers.update({"Content-Type": "application/json"})
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
