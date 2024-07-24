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

    # try:
    #     response: requests.Response = requests.post(
    #         url=endpoint, headers=self.headers, json=post_data
    #     )
    #     response.raise_for_status()
    #     response_content: dict[str, Any] = response.json().values()
    #     if not response_content:
    #         LOG.error("The POST get coverage response is empty")
    #         return None
    #     return CoveragePostResponse(**next(iter(response_content)))
    # except (requests.RequestException, ValueError) as error:
    #     LOG.error(f"Error during coverage POST request: {error}")
    #     return None
