import logging
from functools import wraps
from pydantic import ValidationError
from requests import ConnectionError, HTTPError
from requests.exceptions import MissingSchema

from cg.clients.freshdesk.exceptions import FreshdeskAPIException, FreshdeskModelException

LOG = logging.getLogger(__name__)


def handle_client_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (MissingSchema, HTTPError, ConnectionError) as error:
            LOG.error(f"Request to Freshdesk failed: {error}")
            raise FreshdeskAPIException(error) from error
        except ValidationError as error:
            LOG.error(f"Invalid response from Freshdesk: {error}")
            raise FreshdeskModelException(error) from error
        except Exception as error:
            LOG.error(f"Unexpected error in Freshdesk client: {error}")
            raise FreshdeskAPIException(error) from error

    return wrapper
