""" Test the osticket app """

import logging

import pytest
import requests
from cg.apps.osticket import OsTicket
from cg.exc import TicketCreationError
from requests import Response


def test_osticket_respone_500(monkeypatch, caplog):
    """Test that we log properly when we get a non successful response"""

    # GIVEN a ticket server always gives a failure in response
    osticket_api = OsTicket()
    result = Response
    result.ok = False
    result.reason = "response reason"
    result.text = "response text"
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: result)

    # WHEN we call open_ticket with ok ticket data
    caplog.set_level(logging.ERROR)
    with pytest.raises(TicketCreationError):
        osticket_api.open_ticket(
            name="dummy_name",
            email="dummy_email",
            subject="dummy_subject",
            message="dummy_message",
        )

    # THEN the response text and reason was logged and a ticket creation error raised
    assert result.reason in caplog.text
    assert result.text in caplog.text
