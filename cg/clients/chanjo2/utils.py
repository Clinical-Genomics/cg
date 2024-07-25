"""Chanjo2 client API utility methods."""

import logging
from functools import wraps

from pydantic import ValidationError
from requests import RequestException

from cg.exc import Chanjo2APIClientError, Chanjo2RequestError, Chanjo2ResponseError

LOG = logging.getLogger(__name__)


def handle_client_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RequestException as error:
            LOG.error(f"Request against Chanjo2 API failed: {error}")
            raise Chanjo2RequestError(error) from error
        except ValidationError as error:
            LOG.error(f"Invalidly formatted response from Chanjo2 API: {error}")
            raise Chanjo2ResponseError(error) from error
        except Exception as error:
            LOG.error(f"Unexpected error in Chanjo2 API: {error}")
            raise Chanjo2APIClientError(error) from error

    return wrapper
