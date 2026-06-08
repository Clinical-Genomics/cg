import pytest
from pytest_mock import MockerFixture
from requests import Response

from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.clients.freshdesk.models import TicketResponse


@pytest.fixture
def ticket_raw_response() -> dict:
    return {
        "cc_emails": ["user@cc.com"],
        "fwd_emails": [],
        "reply_cc_emails": ["user@cc.com"],
        "email_config_id": None,
        "fr_escalated": False,
        "group_id": None,
        "priority": 1,
        "requester_id": 1,
        "responder_id": None,
        "source": 2,
        "source_info": 1,
        "spam": False,
        "status": 2,
        "subject": "",
        "company_id": 1,
        "id": 20,
        "type": None,
        "to_emails": None,
        "product_id": None,
        "created_at": "2015-08-24T11:56:51Z",
        "updated_at": "2015-08-24T11:59:05Z",
        "due_by": "2015-08-27T11:30:00Z",
        "fr_due_by": "2015-08-25T11:30:00Z",
        "is_escalated": False,
        "association_type": None,
        "description_text": "Not given.",
        "structured_description": {
            "description_contents": [{"type": "text", "data": {"content": "Not given."}}]
        },
        "description": "<div>Not given.</div>",
        "custom_fields": {"category": "Primary"},
        "tags": [],
        "attachments": [],
    }


def test_get_ticket_success(ticket_raw_response: dict, mocker: MockerFixture):
    # GIVEN a Freshdesk client
    client = FreshdeskClient(
        base_url="https://example.freshdesk.com/api/v2", api_key="test_api_key"
    )
    response = Response()
    response.status_code = 200
    response._content = str.encode(str(ticket_raw_response))
    mocker.patch.object(client.session, "get", return_value=response)

    # WHEN getting a ticket
    ticket_response: TicketResponse = client.get_ticket(1)

    # THEN the response should be a TicketResponse object
    assert isinstance(ticket_response, TicketResponse)
