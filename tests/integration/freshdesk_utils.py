"""Functions that mock responses from the Freshdesk REST API."""

from pytest_httpserver import HTTPServer

from cg.clients.freshdesk.constants import EndPoints, Priority, Status


def expect_freshdesk_get_ticket(
    freshdesk_server: HTTPServer,
    ticket_id: int,
    cc_emails: list[str] | None = None,
    status: int = Status.OPEN,
):
    """Mock the response from Freshdesk for FreshdeskClient.get_ticket.

    Mirrors cg.clients.freshdesk.freshdesk_client.FreshdeskClient.get_ticket, which issues a
    GET to "{base_url}/api/v2/tickets/{ticket_id}".
    """
    freshdesk_server.expect_request(
        f"/freshdesk{EndPoints.TICKETS}/{ticket_id}",
        method="GET",
    ).respond_with_json(_freshdesk_ticket_response(ticket_id, cc_emails, status))


def expect_freshdesk_reply_to_ticket(freshdesk_server: HTTPServer, ticket_id: int):
    """Mock the response from Freshdesk for FreshdeskClient.reply_to_ticket.

    Mirrors cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket, which issues
    a POST to "{base_url}/api/v2/tickets/{ticket_id}/reply". The message body is not matched
    exactly since its contents are dynamically generated from case data.
    """
    freshdesk_server.expect_request(
        f"/freshdesk{EndPoints.TICKETS}/{ticket_id}/reply",
        method="POST",
    ).respond_with_json({"id": ticket_id})


def expect_freshdesk_update_ticket(
    freshdesk_server: HTTPServer,
    ticket_id: int,
    status: int = Status.CLOSED,
    cc_emails: list[str] | None = None,
):
    """Mock the response from Freshdesk for FreshdeskClient.update_ticket.

    Mirrors cg.clients.freshdesk.freshdesk_client.FreshdeskClient.update_ticket, which issues a
    PUT to "{base_url}/api/v2/tickets/{ticket_id}" with a JSON body of {"status": <status>}.
    """
    freshdesk_server.expect_request(
        f"/freshdesk{EndPoints.TICKETS}/{ticket_id}",
        method="PUT",
        json={"status": status},
    ).respond_with_json(_freshdesk_ticket_response(ticket_id, cc_emails, status))


def _freshdesk_ticket_response(ticket_id: int, cc_emails: list[str] | None, status: int) -> dict:
    return {
        "cc_emails": cc_emails or [],
        "id": ticket_id,
        "description": "Integration test ticket",
        "subject": "Integration test ticket",
        "status": status,
        "priority": Priority.LOW,
    }
