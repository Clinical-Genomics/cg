"""Tests for the http utils module."""

import pytest
from requests import HTTPError, Response

from cg.utils.http import raise_for_status_with_body


def test_raise_for_status_with_body_ok_response():
    """Test that no error is raised for a successful response."""
    # GIVEN a response with a successful status code
    response = Response()
    response.status_code = 200

    # WHEN raising for status

    # THEN no error should be raised
    raise_for_status_with_body(response)


def test_raise_for_status_with_body_logs_response_body(caplog):
    """Test that the response body is logged when an HTTPError is raised."""
    # GIVEN a response with a bad status code and a body describing the error
    error_body = b'{"message": "Invalid workflow configuration"}'
    response = Response()
    response.status_code = 400
    response.url = "https://example.com/api/workflow/launch"
    response._content = error_body

    # WHEN raising for status
    with pytest.raises(HTTPError):
        raise_for_status_with_body(response)

    # THEN the response body should be included in the logs
    assert error_body.decode() in caplog.text
