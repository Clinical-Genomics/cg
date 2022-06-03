""" Test the osticket app """

import logging

import pytest

from cg.apps.osticket import OsTicket
from cg.exc import TicketCreationError


def test_osticket_respone_500(monkeypatch, caplog, response):
    """Test that we log properly when we get a non successful response"""

    # GIVEN a ticket server always gives a failure in response
    osticket_api = OsTicket()
    monkeypatch.setattr("requests.post", lambda *args, **kwargs: response)

    # WHEN we call open_ticket with ok ticket data
    caplog.set_level(logging.ERROR)
    with pytest.raises(TicketCreationError):
        osticket_api.open_ticket(
            name="dummy_name",
            email="dummy_email",
            subject="dummy_subject",
            message="dummy_message",
            attachment={},
        )

    # THEN the response text and reason was logged and a ticket creation error raised
    assert response.reason in caplog.text
    assert response.text in caplog.text
