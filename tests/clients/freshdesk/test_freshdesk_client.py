import json
from http import HTTPStatus

import pytest
from pytest_mock import MockerFixture
from requests import Response

from cg.clients.freshdesk.constants import Priority, Status
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.clients.freshdesk.models import TicketResponse
from cg.exc import (
    FreshdeskDeliveryMessageError,
    FreshdeskGetTicketError,
    FreshdeskUpdateTicketError,
)


@pytest.fixture
def ticket_raw_response() -> dict:
    return {
        "cc_emails": ["user@cc.com"],
        "fwd_emails": [],
        "reply_cc_emails": ["user@cc.com"],
        "email_config_id": None,
        "fr_escalated": False,
        "group_id": None,
        "priority": Priority.LOW,
        "requester_id": 1,
        "responder_id": None,
        "source": 2,
        "source_info": 1,
        "spam": False,
        "status": Status.OPEN,
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
    response.status_code = HTTPStatus.OK
    response._content = str.encode(json.dumps(ticket_raw_response))
    mocker.patch.object(client.session, "get", return_value=response)

    # WHEN getting a ticket
    ticket_response: TicketResponse = client.get_ticket(20)

    # THEN the response should be as expected
    expected_ticket_response = TicketResponse(
        id=20,
        cc_emails=["user@cc.com"],
        description="<div>Not given.</div>",
        subject="",
        priority=Priority.LOW,
        status=Status.OPEN,
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
    response.status_code = HTTPStatus.OK
    ticket_raw_response["status"] = 5
    response._content = str.encode(json.dumps(ticket_raw_response))
    mocker.patch.object(client.session, "put", return_value=response)

    # WHEN updating the ticket with a status
    ticket_response = client.update_ticket(
        ticket_id=20, status=Status.CLOSED, cc_emails=["email@to.cc"]
    )

    # THEN the response should be as expected
    expected_ticket_response = TicketResponse(
        id=20,
        cc_emails=["user@cc.com"],
        description="<div>Not given.</div>",
        subject="",
        priority=Priority.LOW,
        status=Status.CLOSED,
    )
    assert ticket_response == expected_ticket_response


def test_update_ticket_failure(mocker: MockerFixture):
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
        client.update_ticket(ticket_id=20, status=Status.CLOSED, cc_emails=["email@to.cc"])


def test_reply_to_ticket_success(mocker: MockerFixture):
    # GIVEN a Freshdesk client
    client = FreshdeskClient(base_url="https://example.freshdesk.com", api_key="test_api_key")

    # GIVEN a successful response
    mocked_response = Response()
    mocked_response.status_code = HTTPStatus.OK
    mocked_post = mocker.patch.object(client.session, "post", return_value=mocked_response)

    # WHEN replying to a ticket with a message
    client.reply_to_ticket(ticket_id=123, message="Reply to ticket", cc_emails=["email@to.cc"])

    # THEN a reply was sent to the ticket
    mocked_post.assert_called_once_with(
        url="https://example.freshdesk.com/api/v2/tickets/123/reply",
        json={"body": "Reply to ticket", "cc_emails": ["email@to.cc"]},
    )


def test_reply_to_ticket_failure(mocker: MockerFixture):
    # GIVEN a Freshdesk client
    client = FreshdeskClient(base_url="https://example.freshdesk.com", api_key="test_api_key")

    # GIVEN a failing HTTP response
    response = Response()
    response.status_code = HTTPStatus.BAD_REQUEST
    mocker.patch.object(client.session, "post", return_value=response)

    # WHEN replying to the ticket with a message
    # THEN a FreshdeskDeliveryMessageError should be raised
    with pytest.raises(FreshdeskDeliveryMessageError):
        client.reply_to_ticket(ticket_id=20, message="", cc_emails=[])
