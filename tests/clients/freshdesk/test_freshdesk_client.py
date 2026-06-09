import json
from http import HTTPStatus

import pytest
from pytest_mock import MockerFixture
from requests import Response

from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.clients.freshdesk.models import TicketResponse
from cg.exc import FreshdeskGetTicketError, FreshdeskUpdateTicketError


@pytest.fixture
def ticket_raw_response() -> dict:
    return {
        "ticket": {
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
    }


def test_get_ticket_success(ticket_raw_response: dict, mocker: MockerFixture):
    # GIVEN a Freshdesk client
    client = FreshdeskClient(
        base_url="https://example.freshdesk.com/api/v2", api_key="test_api_key"
    )
    response = Response()
    response.status_code = 200
    response._content = str.encode(json.dumps(ticket_raw_response))
    mocker.patch.object(client.session, "get", return_value=response)

    # WHEN getting a ticket
    ticket_response: TicketResponse = client.get_ticket(20)

    # THEN the response should be a TicketResponse object
    expected_ticket_response = TicketResponse(
        id=20, description="<div>Not given.</div>", subject="", priority=1, status=2
    )
    assert ticket_response == expected_ticket_response


def test_get_ticket_failure(mocker: MockerFixture):
    # GIVEN a Freshdesk client
    client = FreshdeskClient(
        base_url="https://example.freshdesk.com/api/v2", api_key="test_api_key"
    )

    # GIVEN that the HTTP request returns an internal server error
    response = Response()
    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    mocker.patch.object(client.session, "get", return_value=response)

    # WHEN getting a ticket
    # THEN a FreshdeskGetTicketError should be raised
    with pytest.raises(FreshdeskGetTicketError):
        client.get_ticket(20)


def test_update_ticket_success(ticket_raw_response: dict, mocker: MockerFixture):
    # GIVEN a Freshdesk client
    client = FreshdeskClient(
        base_url="https://example.freshdesk.com/api/v2", api_key="test_api_key"
    )

    # GIVEN a successful HTTP response
    response = Response()
    response.status_code = 200
    ticket_raw_response["ticket"]["status"] = 5
    response._content = str.encode(json.dumps(ticket_raw_response))
    mocker.patch.object(client.session, "put", return_value=response)

    # WHEN updating the ticket with a status
    ticket_response = client.update_ticket(ticket_id=20, status=5)

    # THEN the response should be a TicketResponse object
    expected_ticket_response = TicketResponse(
        id=20, description="<div>Not given.</div>", subject="", priority=1, status=5
    )
    assert ticket_response == expected_ticket_response


def test_update_ticket_failure(ticket_raw_response: dict, mocker: MockerFixture):
    # GIVEN a Freshdesk client
    client = FreshdeskClient(
        base_url="https://example.freshdesk.com/api/v2", api_key="test_api_key"
    )

    # GIVEN a failing HTTP response
    response = Response()
    response.status_code = HTTPStatus.BAD_REQUEST
    mocker.patch.object(client.session, "put", return_value=response)

    # WHEN updating the ticket with a status
    # THEN a FreshdeskUpdateTicketError should be raised
    with pytest.raises(FreshdeskUpdateTicketError):
        client.update_ticket(ticket_id=20, status=5)
