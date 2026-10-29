"""Helper functions for working with the requests library."""

import logging

from requests import HTTPError, Response

LOG = logging.getLogger(__name__)


def raise_for_status_with_body(response: Response) -> None:
    """Raises an HTTPError for bad responses, logging the response body as it contains the actual error."""
    try:
        response.raise_for_status()
    except HTTPError as error:
        LOG.exception(f"{error} - Response body: {response.text}")
        raise
