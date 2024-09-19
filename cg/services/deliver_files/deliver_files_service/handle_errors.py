import logging
from functools import wraps

from pydantic_core import ValidationError


LOG = logging.getLogger(__name__)


def handle_delivery_errors(func):
    """
    Log an error when a Housekeeper bundle version is missing.

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as error:
            LOG.warning(error)
            return

    return wrapper
