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

    def create_ticket(self, ticket: TicketCreate) -> TicketResponse:
        """Create a ticket."""
        LOG.debug(ticket.model_dump_json())
        session: Session = self._get_session()
        try:
            response: Response = session.post(
                url=f"{self.base_url}{EndPoints.TICKETS}",
                json=ticket.model_dump(exclude_none=True),
            )
            response.raise_for_status()
            ticket_response: TicketResponse = TicketResponse.model_validate(response.json())
            return ticket_response
        except RequestException as error:
            LOG.error(f"Could not create ticket: {error}")
            raise FreshdeskAPIException(error) from error
        except ValidationError as error:
            LOG.error(f"Response from Freshdesk does not fit model: {TicketResponse}.\n{error}")
            raise FreshdeskModelException(error) from error
        finally:
            session.close()

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
            status_forcelist=[HTTPStatus.TOO_MANY_REQUESTS],
            allowed_methods=None,
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
